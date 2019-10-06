from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
engine = create_engine('sqlite:///database.db')
meta = MetaData()

user = Table(
   'user', meta,
   Column('number', String, primary_key=True),
   Column('username', String, unique=True),
   Column('language', String),
)

friends = Table(
   'friends', meta,
   Column('username', String, primary_key=True),
   Column('friend_username', String, nullable=False),
)

meta.create_all(engine)
