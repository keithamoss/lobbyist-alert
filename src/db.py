from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AppSettings(Base):
  __tablename__ = "app-settings"
  key = Column(String, primary_key=True)
  val = Column(String)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    added_on = Column(DateTime, default=func.now())

    @validates('email')
    def validate_email(self, key, email):
      from email.utils import parseaddr
      if '@' not in parseaddr(email)[1]:
          raise Exception("Email address '" + email + "' not valid.")
      return email

from sqlalchemy import create_engine
engine = create_engine('sqlite:///db.sqlite')

from sqlalchemy.orm import sessionmaker
Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)
