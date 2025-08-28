"""
SQLAlchemy backend

Disk usage with sqlite-driver:

JSON string with about 122 characters per record:

10.000 records: 3 MB
100.000 records: 30 MB
1.000.000 records: 310 MB

roughly 300 bytes per record


JSON string with about 244 characters per record:

10.000 records: 4 MB
100.000 records: 43 MB
1.000.000 records: 431 MB

roughly 400 bytes per record

Presumably, 180 bytes + JSON string size per record.

"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

from sqlalchemy import (
    JSON,
    String,
    create_engine,
    distinct,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    load_only,
    mapped_column,
)

from dump_things_service.backends import (
    BackendResultList,
    RecordInfo,
    ResultListInfo,
    StorageBackend,
    create_sort_key,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


record_file_name = '.sqlite-records.db'


class Base(DeclarativeBase):
    pass


class Thing(Base):
    __tablename__ = 'thing'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    iri: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    class_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    object: Mapped[dict] = mapped_column(JSON, nullable=False)
    sort_key: Mapped[str] = mapped_column(nullable=False)


class SQLResultList(BackendResultList):
    def __init__(
        self,
        engine: Any,
    ):
        super().__init__()
        self.engine = engine

    def generate_result(
        self,
        _: int,
        iri: str,
        class_name: str,
        sort_key: str,
        db_id: int,
    ) -> RecordInfo:
        """
        Generate a JSON representation of the record at index `index`.

        :param _: The index of the record.
        :param iri: The IRI of the record.
        :param class_name: The class name of the record.
        :param sort_key: The sort key for the record.
        :param db_id: The id of the record in the database
        :return: A RecordInfo object.
        """
        with Session(self.engine) as session, session.begin():
            thing = session.get(Thing, db_id)
            return RecordInfo(
                iri=iri,
                class_name=class_name,
                json_object=thing.object,
                sort_key=sort_key,
            )


class _SQLiteBackend(StorageBackend):
    def __init__(
        self,
        db_path: Path,
        *,
        order_by: Iterable[str] | None = None,
        echo: bool = False,
    ) -> None:
        super().__init__(order_by=order_by)
        self.db_path = db_path
        self.engine = create_engine('sqlite:///' + str(db_path), echo=echo)
        Base.metadata.create_all(self.engine)

    def add_record(
        self,
        iri: str,
        class_name: str,
        json_object: dict,
    ):
        with Session(self.engine) as session, session.begin():
            self._add_record_with_session(
                session=session,
                iri=iri,
                class_name=class_name,
                json_object=json_object,
            )

    def add_records_bulk(
        self,
        record_infos: Iterable[RecordInfo],
    ):
        with Session(self.engine) as session, session.begin():
            for record_info in record_infos:
                self._add_record_with_session(
                    session=session,
                    iri=record_info.iri,
                    class_name=record_info.class_name,
                    json_object=record_info.json_object,
                )

    def _add_record_with_session(
        self,
        session: Session,
        iri: str,
        class_name: str,
        json_object: dict,
    ):
        sort_key = create_sort_key(json_object, self.order_by)
        existing_record = session.query(Thing).filter_by(iri=iri).first()
        if existing_record:
            existing_record.class_name = class_name
            existing_record.object = json_object
            existing_record.sort_key = sort_key
        else:
            session.add(
                Thing(
                    iri=iri,
                    class_name=class_name,
                    object=json_object,
                    sort_key=sort_key,
                )
            )

    def get_record_by_iri(
        self,
        iri: str,
    ) -> RecordInfo | None:
        with Session(self.engine) as session, session.begin():
            statement = select(Thing).filter_by(iri=iri)
            thing = session.scalar(statement)
            if thing:
                return RecordInfo(
                    iri=thing.iri,
                    class_name=thing.class_name,
                    json_object=thing.object,
                    sort_key=thing.sort_key,
                )
        return None

    def get_records_of_classes(
        self,
        class_names: Iterable[str],
        pattern: str | None = None,
    ) -> SQLResultList:

        if pattern is None:
            statement = select(Thing).where(Thing.class_name.in_(class_names))
        else:
            # The SQLAlchemy code implements the following SQL query:
            # select distinct * from thing where lower(json(thing.object)) like lower('<pattern>');
            statement = select(Thing).distinct().where(func.json(Thing.object).ilike(pattern))
            # TODO: `statement` above should be changed to implement:
            #  select distinct * from thing, json_tree(thing.object) where lower(json_tree.value) like lower('<pattern>');

        for attribute in self.order_by:
            statement = statement.order_by(Thing.object[attribute]).options(
                load_only(Thing.id)
            )
        with Session(self.engine) as session, session.begin():
            return SQLResultList(self.engine).add_info(
                ResultListInfo(
                    iri=thing.iri,
                    class_name=thing.class_name,
                    sort_key=thing.sort_key,
                    private=thing.id,
                )
                for thing in session.scalars(statement).all()
            )

    def get_all_records(
        self,
    ) -> SQLResultList:
        statement = select(Thing)
        for attribute in self.order_by:
            statement = statement.order_by(Thing.object[attribute]).options(
                load_only(Thing.id)
            )
        with Session(self.engine) as session, session.begin():
            return SQLResultList(self.engine).add_info(
                ResultListInfo(
                    iri=thing.iri,
                    class_name=thing.class_name,
                    sort_key=thing.sort_key,
                    private=thing.id,
                )
                for thing in session.scalars(statement).all()
            )


# Ensure that there is only one SQL-backend per database file.
_existing_sqlite_backends = {}


def SQLiteBackend(  # noqa: N802
    db_path: Path, *, order_by: Iterable[str] | None = None, echo: bool = False
) -> _SQLiteBackend:
    existing_backend = _existing_sqlite_backends.get(db_path)
    if not existing_backend:
        existing_backend = _SQLiteBackend(
            db_path=db_path,
            order_by=order_by,
            echo=echo,
        )
        _existing_sqlite_backends[db_path] = existing_backend

    if existing_backend.order_by != (order_by or ['pid']):
        msg = f'Store at {db_path} already exists with different order specification.'
        raise ValueError(msg)

    return existing_backend
