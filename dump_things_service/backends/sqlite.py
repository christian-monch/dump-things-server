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

from collections.abc import Iterable
from typing import Any

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

from dump_things_service.lazy_list import LazyList


class Base(DeclarativeBase):
    pass


class Thing(Base):
    __tablename__ = 'thing'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    iri: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    class_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    object: Mapped[dict] = mapped_column(JSON, nullable=False)


class LazySQLList(LazyList):
    def __init__(
            self,
            engine: Any,
    ):
        super().__init__()
        self.engine = engine

    def generate_element(self, index: int, info: Any) -> Any:
        with Session(self.engine) as session, session.begin():
            thing = session.get(Thing, info)
            return thing.class_name, thing.object


class SQLiteBackend:
    def __init__(self, db_path: str, *, echo: bool = False) -> None:
        self.engine = create_engine('sqlite:///' + db_path, echo=echo)
        Base.metadata.create_all(self.engine)
        self._session = None

    def add_data(
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
                )
            )

    def add_data_bulk(
        self,
        object_info: Iterable[tuple[str, str, dict]],
    ):
        with Session(self.engine) as session, session.begin():
            for iri, class_name, json_object in object_info:
                session.add(
                    Thing(
                        iri=iri,
                        class_name=class_name,
                        object=json_object,
                    )
                )

    def get_record_by_iri(
        self,
        iri: str,
    ) -> tuple[str, dict] | None:
        with Session(self.engine) as session, session.begin():
            statement = select(Thing).filter_by(iri=iri)
            thing = session.scalar(statement)
            return str(thing.class_name), thing.object if thing else None

    def get_records_of_class(
            self,
            class_name: str,
            order_by: Iterable[str] | None = None,
    ) -> LazySQLList:
        statement = select(Thing).filter_by(class_name=class_name)
        for attribute in order_by or ['pid']:
            statement = statement.order_by(Thing.object[attribute]).options(load_only(Thing.id))
        with Session(self.engine) as session, session.begin():
            return LazySQLList(self.engine).add_info(
                (thing.id for thing in session.scalars(statement).all())
            )
