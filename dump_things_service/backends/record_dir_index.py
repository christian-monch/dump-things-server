"""
A disk based index that associates IRIs with paths and sort-keys.

It is mainly used in `RecordDirStore` to quickly access records by their IRIs,
and has been externalized to cleanly isolate the index rebuilding logic from
`RecordDirStore`. The reason is that index rebuilding from disk requires a
schema because it has to resolve CURIEs in the records, i.e. the `pid`-entries.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import yaml
from sqlalchemy import (
    create_engine,
    delete,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
)

from dump_things_service import config_file_name
from dump_things_service.backends import create_sort_key
from dump_things_service.model import get_model_for_schema
from dump_things_service.resolve_curie import resolve_curie

if TYPE_CHECKING:
    from collections.abc import (
        Generator,
        Iterable,
    )
    from pathlib import Path


__all__ = [
    'IndexEntry',
    'RecordDirIndex',
]

index_file_name = '.directory_dir_index.db'
ignored_files = {'.', '..', config_file_name, index_file_name}

lgr = logging.getLogger('dump_things_service')


class Base(DeclarativeBase):
    pass


class IndexEntry(Base):
    __tablename__ = 'index_entry'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    iri: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    class_name: Mapped[str] = mapped_column(nullable=False)
    path: Mapped[str] = mapped_column(nullable=False)
    sort_key: Mapped[str] = mapped_column(nullable=False)


class RecordDirIndex:
    def __init__(
        self,
        store_dir: Path,
        suffix: str,
        *,
        echo: bool = False,
    ):
        if not store_dir.is_absolute():
            msg = f'Not an absolute path: {store_dir}'
            raise ValueError(msg)
        if not store_dir.exists():
            msg = f'Path does not exist: {store_dir}'
            raise ValueError(msg)
        if not store_dir.is_dir():
            msg = f'Not a directory: {store_dir}'
            raise ValueError(msg)

        self.store_dir = store_dir
        self.suffix = suffix
        self.needs_rebuild = not (store_dir / index_file_name).exists()
        self.engine = create_engine(
            'sqlite:///' + str(store_dir / index_file_name),
            echo=echo,
        )
        Base.metadata.create_all(self.engine)

    def add_iri_info(
        self,
        iri: str,
        class_name: str,
        path: str,
        sort_key: str,
    ):
        with Session(self.engine) as session, session.begin():
            self.add_iri_info_with_session(
                session,
                iri=iri,
                class_name=class_name,
                path=path,
                sort_key=sort_key,
            )

    def add_iri_info_with_session(
        self,
        session: Session,
        iri: str,
        class_name: str,
        path: str,
        sort_key: str,
    ):
        existing_record = session.query(IndexEntry).filter_by(iri=iri).first()
        if existing_record:
            if existing_record.path != path:
                msg = f'Duplicated IRI ({iri}): already indexed record {existing_record.path} has the same IRI as new record at {path}.'
                raise ValueError(msg)
            existing_record.sort_key = sort_key
        else:
            session.add(
                IndexEntry(
                    iri=iri,
                    class_name=class_name,
                    path=path,
                    sort_key=sort_key,
                )
            )

    def get_info_for_iri(
        self,
        iri: str,
    ) -> tuple | None:
        with Session(self.engine) as session, session.begin():
            statement = select(IndexEntry).filter_by(iri=iri)
            entry = session.scalar(statement)
            if entry:
                return entry.class_name, entry.path, entry.sort_key
            return None

    def get_info_for_class(
        self,
        class_name: str,
    ) -> Generator[IndexEntry]:
        with Session(self.engine) as session, session.begin():
            statement = select(IndexEntry).filter_by(class_name=class_name)
            result = session.execute(statement)
            for row in result:
                yield row[0]

    def get_info_for_all_classes(
        self,
    ) -> Generator[IndexEntry]:
        with Session(self.engine) as session, session.begin():
            statement = select(IndexEntry)
            result = session.execute(statement)
            for row in result:
                yield row[0]

    def rebuild_index(
        self,
        schema: str,
        order_by: Iterable[str] | None = None,
    ):
        """Rebuild the index from the records in the directory."""
        lgr.info('Building IRI index for records in %s', self.store_dir)

        order_by = order_by or ['pid']

        model = get_model_for_schema(schema)[0]
        with Session(self.engine) as session, session.begin():
            statement = delete(IndexEntry)
            session.execute(statement)

            for path in self.store_dir.rglob(f'*.{self.suffix}'):
                if path.is_file() and path.name not in ignored_files:
                    try:
                        # Catch YAML structure errors
                        record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                    except Exception as e:  # noqa: BLE001
                        lgr.error('Error: reading YAML record from %s: %s', path, e)
                        continue

                    try:
                        # Catch YAML payload errors
                        pid = record['pid']
                    except (TypeError, KeyError):
                        lgr.error(
                            'Error: record at %s does not contain a mapping with `pid`',
                            path,
                        )
                        continue

                    iri = resolve_curie(model, pid)
                    class_name = self._get_class_name(path)
                    sort_key = create_sort_key(record, order_by)

                    # Log errors and continue building the index
                    try:
                        session.add(
                            IndexEntry(
                                iri=iri,
                                path=str(path),
                                class_name=class_name,
                                sort_key=sort_key,
                            )
                        )
                    except ValueError as e:
                        lgr.error('Error during index creation: %s', e)
        lgr.info('Index built')
        self.needs_rebuild = False

    def rebuild_if_needed(
        self,
        schema: str,
        order_by: Iterable[str] | None = None,
    ):
        if self.needs_rebuild:
            self.rebuild_index(schema=schema, order_by=order_by)
            self.needs_rebuild = False

    def _get_class_name(self, path: Path) -> str:
        """Get the class name from the path."""
        rel_path = path.absolute().relative_to(self.store_dir)
        return rel_path.parts[0]
