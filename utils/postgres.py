import logging
import re
from typing import List, Type, Union
from sqlalchemy import create_engine, Column, Boolean, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import env


logger = logging.getLogger(env.ENV_NAME)


### DB SETUP ###

url = re.sub('postgres', 'postgresql', env.DATABASE_URL) # workaround for heroku-managed db url
engine = create_engine(url, echo=False)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
Base = declarative_base()


class Park(Base):
    __tablename__ = 'parks'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    rides = relationship("Ride", passive_deletes=True, backref="park")
    alerts = relationship("Alert", passive_deletes=True, backref="park")
    def __repr__(self):
        return f"{self.name} ({self.id})"


class Ride(Base):
    __tablename__ = 'rides'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    park_id = Column(Integer, ForeignKey("parks.id", ondelete='CASCADE'), nullable=False)
    wait_time = Column(Integer, nullable=False)
    is_open = Column(Boolean, nullable=False)
    def __repr__(self):
        return f"{self.name} ({self.id} @ {self.park_id}) - [{'OPEN: ' + self.wait_time + 'm' if self.is_open else 'CLOSED'}]"


class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(String, primary_key=True)
    ride_id = Column(Integer, ForeignKey("rides.id", ondelete='CASCADE'), nullable=False)
    park_id = Column(Integer, ForeignKey("parks.id", ondelete='CASCADE'), nullable=False)
    phone_number = Column(String, nullable=False)
    wait_time = Column(Integer, nullable=False)
    expiration = Column(Integer, nullable=False)
    def __repr__(self):
        return f"[{self.id}] {self.phone_number} ({self.ride_id} @ {self.park_id}) - {self.wait_time} by {self.expiration}"


Base.metadata.create_all(bind=engine)


### DB WRAPPERS ###


class CrudUtils:
    def _create_objects(objs:List[Union[Park, Ride, Alert]]) -> List[Union[Park, Ride, Alert]]:
        with SessionLocal() as db:
            for obj in objs:
                db.add(obj)
            db.commit()
            for obj in objs:
                db.refresh(obj)
        return objs

    def create_park(**kwargs) -> Park:
        return CrudUtils._create_objects([
            Park(**kwargs),
        ])

    def create_ride(**kwargs) -> Ride:
        return CrudUtils._create_objects([
            Ride(**kwargs),
        ])

    def create_alert(**kwargs) -> Alert:
        return CrudUtils._create_objects([
            Alert(**kwargs),
        ])

    def _read_objects(ctype:Type[Union[Park, Ride, Alert]], filters:dict[str:str]) -> List[Union[Park, Ride, Alert]]:
        with SessionLocal() as db:
            q = db.query(ctype)
            for k,v in filters.items():
                q.filter(ctype.__dict__[k] == v)
            return q.all()

    def read_parks(**kwargs) -> List[Park]:
        return CrudUtils._read_objects(Park, kwargs)

    def read_rides(**kwargs) -> List[Ride]:
        return CrudUtils._read_objects(Ride, kwargs)

    def read_alerts(**kwargs) -> List[Alert]:
        return CrudUtils._read_objects(Alert, kwargs)

    def _update_objects(ctype:Type[Union[Park, Ride, Alert]], filters:dict[str:str], updates:dict[str:str]) -> List[Union[Park, Ride, Alert]]:
        logger.debug(filters)
        with SessionLocal() as db:
            q = db.query(ctype)
            for k,v in filters.items():
                q = q.with_transformation(lambda q:q.filter(ctype.__dict__[k] == v))
            objs = q.with_transformation(lambda q:q.all())
            for obj in objs:
                for k,v in updates.items():
                    setattr(obj, k, v)
            db.commit()
            for obj in objs:
                db.refresh(obj)
        return objs

    def update_parks(updates:dict[str:str]={}, **kwargs) -> Park:
        return CrudUtils._update_objects(Park, filters=kwargs, updates=updates)[0]

    def update_rides(updates:dict[str:str]={}, **kwargs) -> Ride:
        return CrudUtils._update_objects(Ride, filters=kwargs, updates=updates)[0]

    def update_alerts(updates:dict[str:str]={}, **kwargs) -> Alert:
        return CrudUtils._update_objects(Alert, filters=kwargs, updates=updates)[0]

    def _delete_objects(ctype:Type[Union[Park, Ride, Alert]], filters:dict[str:str]) -> List[Union[Park, Ride, Alert]]:
        with SessionLocal() as db:
            q = db.query(ctype)
            for k,v in filters.items():
                q.with_transformation(lambda q:q.filter(ctype.__dict__[k] == v))
            objs = q.with_transformation(lambda q:q.all())
            for obj in objs:
                db.delete(obj)
            db.commit()
        return objs

    def delete_parks(**kwargs) -> List[Union[Park, Ride, Alert]]:
        return CrudUtils._delete_objects(Park, filters=kwargs)

    def delete_rides(**kwargs) -> List[Union[Park, Ride, Alert]]:
        return CrudUtils._delete_objects(Ride, filters=kwargs)

    def delete_alerts(**kwargs) -> List[Union[Park, Ride, Alert]]:
        return CrudUtils._delete_objects(Alert, filters=kwargs)