from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
engine = create_engine('sqlite:///college.db', echo = True)
meta = MetaData()

user = Table(
   'user', meta,
   Column('username', Integer, primary_key=True),
   Column('number', String, unique=True, nullable=False),
   Column('language', String),
)

friends = Table(
   'friends', meta,
   Column('username', Integer, primary_key=True),
   Column('friend_username', String, nullable=False),
)

meta.create_all(engine)
