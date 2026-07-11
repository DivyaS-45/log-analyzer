from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Upload(Base):

    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True)

    filename = Column(String)

    info_count = Column(Integer)

    warning_count = Column(Integer)

    error_count = Column(Integer)
    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )



class Error(Base):

    __tablename__ = "errors"

    id = Column(Integer, primary_key=True)

    upload_id = Column(
        Integer,
        ForeignKey("uploads.id")
    )

    error_message = Column(Text)

    occurrence_count = Column(Integer)
