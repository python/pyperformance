import perf.text_runner
from six.moves import xrange

from sqlalchemy import Column, ForeignKey, Integer, String, Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


metadata = MetaData()

Person = Table('person', metadata,
               Column('id', Integer, primary_key=True),
               Column('name', String(250), nullable=False))

Address = Table('address', metadata,
                Column('id', Integer, primary_key=True),
                Column('street_name', String(250)),
                Column('street_number', String(250)),
                Column('post_code', String(250), nullable=False),
                Column('person_id', Integer, ForeignKey('person.id')))

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite://')

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
metadata.create_all(engine)


# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# add 'npeople' people to the database
def main(npeople):
    # Insert a Person in the person table
    new_person = Person.insert()
    new_person.execute(name="name")

    # Insert an Address in the address table
    new_address = Address.insert()
    new_address.execute(post_code='00000')

    # do 'npeople' queries per insert
    for i in xrange(npeople):
        s = Person.select()
        s.execute()


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='sqlalchemy_imperative')
    runner.metadata['description'] = ("SQLAlchemy Imperative benchmark "
                                      "using SQLite")

    npeople = 100
    runner.bench_func(main, npeople)
