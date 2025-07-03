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

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
)

from sqlalchemy import (
    JSON,
    String,
    create_engine,
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
    RecordInfo,
    StorageBackend, create_sort_key,
)
from dump_things_service.lazy_list import LazyList

if TYPE_CHECKING:
    from collections.abc import Iterable


class Base(DeclarativeBase):
    pass


class Thing(Base):
    __tablename__ = 'thing'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    iri: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    class_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    object: Mapped[dict] = mapped_column(JSON, nullable=False)
    sort_key: Mapped[str] = mapped_column(nullable=False)


class LazySQLList(LazyList):
    def __init__(
        self,
        engine: Any,
    ):
        super().__init__()
        self.engine = engine

    def generate_element(self, _: int, info: Any) -> Any:
        with Session(self.engine) as session, session.begin():
            iri, table_id, sort_key = info
            thing = session.get(Thing, table_id)
            #json_object = thing.object
            #if 'schema_type' not in json_object:
            #    json_object['schema_type'] = _get_schema_type(
            #        thing.class_name,
            #        self.schema_model
            #    )
            return RecordInfo(
                iri=thing.iri, class_name=thing.class_name, json_object=thing.object, sort_key=thing.sort_key
            )

    def unique_identifier(self, info: Any) -> Any:
        # Return the IRI as unique identifier
        return info[0]

    def sort_key(self, info: Any) -> str:
        # Return the sort_key entry as sort key
        return info[2]


class SQLiteBackend(StorageBackend):
    def __init__(
        self,
        db_path: Path,
        *,
        order_by: Iterable[str] | None = None,
        echo: bool = False
    ) -> None:
        super().__init__(order_by=order_by)
        self.engine = create_engine('sqlite:///' + str(db_path), echo=echo)
        Base.metadata.create_all(self.engine)

    def add_record(
        self,
        iri: str,
        class_name: str,
        json_object: dict,
    ):
        with Session(self.engine) as session, session.begin():
            session.add(
                Thing(
                    iri=iri,
                    class_name=class_name,
                    object=json_object,
                    sort_key=create_sort_key(json_object, self.order_by),
                )
            )

    def add_records_bulk(
        self,
        record_infos: Iterable[RecordInfo],
    ):
        with Session(self.engine) as session, session.begin():
            for record_info in record_infos:
                session.add(
                    Thing(
                        iri=record_info.iri,
                        class_name=record_info.class_name,
                        object=record_info.json_object,
                        sort_key=create_sort_key(record_info.json_object, self.order_by),
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
    ) -> LazySQLList[RecordInfo]:
        statement = select(Thing).where(Thing.class_name.in_(class_names))
        for attribute in self.order_by:
            statement = statement.order_by(Thing.object[attribute]).options(
                load_only(Thing.id)
            )
        with Session(self.engine) as session, session.begin():
            return LazySQLList(self.engine).add_info(
                (thing.iri, thing.id, thing.sort_key)
                for thing in session.scalars(statement).all()
            )
