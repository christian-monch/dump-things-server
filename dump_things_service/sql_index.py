from __future__ import annotations

from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


TYPE_NONE = 0
TYPE_INT = 1
TYPE_FLOAT = 2
TYPE_STR = 3
TYPE_MAPPING = 4
TYPE_SEQUENCE = 5


class Base(DeclarativeBase):
    pass


class IdSource(Base):
    __tablename__ = 'id_source'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    def __repr__(self) -> str:
        return f'IdSource(id={self.id!r})'


class Value(Base):
    __tablename__ = 'value'

    value_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[int] = mapped_column(Integer, default=TYPE_STR)
    value_int: Mapped[Optional[int]] = mapped_column(default=None)
    value_float: Mapped[Optional[float]] = mapped_column(default=None)
    value_str: Mapped[Optional[str]] = mapped_column(default=None)
    value_mapping: Mapped[Optional[int]] = mapped_column(ForeignKey('mapping.object_id'))
    value_list: Mapped[Optional[int]] = mapped_column(ForeignKey('sequence.list_id'))


class Mapping(Base):
    __tablename__ = 'mapping'

    mapping_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    object_id: Mapped[int] = mapped_column(nullable=False)
    key: Mapped[str]
    value: Mapped[int] = mapped_column(ForeignKey('value.value_id'))

    def __repr__(self) -> str:
        return f'Mapping(id={self.mapping_id!r}, key={self.key!r}, value={self.value!r})'


class Sequence(Base):
    __tablename__ = 'sequence'

    sequence_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(nullable=False)
    index: Mapped[int] = mapped_column(nullable=False, default=0)
    value: Mapped[int] = mapped_column(ForeignKey('value.value_id'))

    def __repr__(self) -> str:
        return f'Sequence(id={self.sequence_id!r}, list_id={self.list_id}, index={self.index!r}, value={self.value!r})'


class Record(Base):
    __tablename__ = 'record'

    pid: Mapped[str] = mapped_column(primary_key=True)
    class_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[int] = mapped_column(ForeignKey('mapping.object_id'))

    def __repr__(self) -> str:
        return f"Record(pid={self.pid!r}, class_name={self.class_name!r}, content={self.record_id!r})"


def add_data(
        session: Session,
        data: dict | list | int | float | str,
) -> int:
    if isinstance(data, dict):
        new_mapping_id = IdSource()
        session.add(new_mapping_id)
        session.commit()
        #print('Generated new mapping ID:', new_mapping_id)
        for key, value in data.items():
            db_value = add_data(session, value)
            mapping_entry = Mapping(object_id=new_mapping_id.id, key=key, value=db_value)
            session.add(mapping_entry)

        result_value = Value(type=TYPE_MAPPING, value_mapping=new_mapping_id.id)

    elif isinstance(data, list):
        new_sequence_id = IdSource()
        session.add(new_sequence_id)
        session.commit()
        #print('Generated new sequence ID:', new_sequence_id)
        for index, value in enumerate(data):
            db_value = add_data(session, value)
            sequence_entry = Sequence(list_id=new_sequence_id.id, index=index, value=db_value)
            session.add(sequence_entry)
        result_value = Value(type=TYPE_SEQUENCE, value_list=new_sequence_id.id)

    elif isinstance(data, int):
        result_value = Value(type=TYPE_INT, value_int=data)

    elif isinstance(data, float):
        result_value = Value(type=TYPE_INT, value_float=data)

    elif isinstance(data, str):
        result_value = Value(type=TYPE_STR, value_str=data)

    elif isinstance(data, None):
        result_value = Value(type=TYPE_NONE)

    else:
        raise ValueError(f'Unsupported data type: {type(data)}')

    session.add(result_value)
    session.commit()
    return result_value.value_id


#engine = create_engine('sqlite:///:memory:', echo=False)
#engine = create_engine('sqlite:////tmp/test-2.db', echo=True)
engine = create_engine('sqlite:////tmp/test-2.db', echo=False)
Base.metadata.create_all(engine)


pid_template = 'trr379:person_{i}'
name_template = 'name_{i}'

data = {
    'pid': 'trr379:person_2',
    'name': 'name_2',
    'content': {
        'a': 1,
        'b': 2.5,
        'list_1': [1, 2, 3],
    },
}


with Session(engine) as session:
    for i in range(10000):
        data['pid'] = pid_template.format(i=i)
        data['name'] = name_template.format(i=i)
        value = add_data(session, data)
        #print(value)
        session.commit()
        if i % 100 == 0:
            print(f'Added {i} records')
