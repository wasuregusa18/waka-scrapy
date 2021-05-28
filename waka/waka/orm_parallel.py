import os
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import UniqueConstraint

user = os.environ["USER"]
password = os.environ["PASSWORD"]
database_name = os.environ["DATABASE_NAME"]

connect_string = f"mysql+mysqldb://{user}:{password}@localhost/{database_name}?charset=utf8mb4"
engine = create_engine(connect_string, echo=False,encoding="utf8")  # echo will spit out actual sql code
Base = declarative_base()


# collection_contents = Table("collection_contents",Base.metadata,
#     Column("collection_id",Integer,ForeignKey('collections.id')),
#     Column("poem_id",Integer,ForeignKey('poems.id')),
#     Column("position",Integer)
# )

collection_authors = Table("collection_authors",Base.metadata,
    Column("collection_id",String(255),ForeignKey('collections.id')),
    Column("poet_id",String(255),ForeignKey('poets.id')),
    UniqueConstraint('collection_id', 'poet_id', name='No_dup')
)


class CollectionContent(Base): #this is the association table linking poem and collection
    __tablename__ = "collection_contents" 

    id = Column(Integer,primary_key=True)
    collection_id = Column(String(255),ForeignKey('collections.id'))
    poem_id = Column(String(255),ForeignKey('poems.id'))
    position = Column(String(25))

    collection = relationship("Collection",back_populates="poems")
    poem = relationship("Poem",back_populates="collections")

    __table_args__ = (UniqueConstraint('collection_id', 'poem_id', name='No_dup'),)
    
    def __repr__(self) -> str:
        return f"<CollectionContent(Collection={self.collection.title}, Poem={self.poem.poem}{', Position=' +str(self.position) if self.position else ''}"


class Poet(Base):
    """actual database also has last_modified and first_scrapped"""
    __tablename__ = "poets"
    id = Column(String(255),primary_key=True)
    kanji = Column(String(25),nullable=False,unique=True)
    hiragana = Column(String(50),nullable=False)
    bio = Column(Text)
    dates = Column(String(25))
    jidai = Column(String(10))
    alias = Column(String(255))
    link = Column(String(2550), nullable=False)
    
    poems = relationship("Poem",back_populates="poet")
    collections = relationship("Collection",secondary=collection_authors)

    def __repr__(self) -> str:
        return f"<Poet(kanji={self.kanji}, hiragana={self.hiragana}, poem_count={len(self.poems)})>"



class Poem(Base):
    __tablename__ = "poems"
    id = Column(String(255),primary_key=True)
    title = Column(Text)
    poem = Column(String(255),nullable=False,unique=True)
    mean = Column(String(2550))
    # other = Column(String(255))
    hasei = Column(Text)
    honka = Column(String(2550))
    note = Column(Text)
    satyu = Column(String(255))
    appre = Column(Text)
    poet_id = Column(String(255),ForeignKey("poets.id"),nullable=False, unique=True)
    link = Column(String(2550),nullable=False)

    poet = relationship("Poet",back_populates="poems")
    collections = relationship("CollectionContent",back_populates="poem")

    def __repr__(self) -> str:
        return f"<Poem(poem={self.poem}, poet={self.poet.kanji}>"

class Collection(Base):
    __tablename__ = "collections"
    id = Column(String(255),primary_key=True)
    title = Column(String(255),nullable=False,unique=True)
    history = Column(Text)
    dates = Column(String(25))
    alias = Column(String(255))
    link = Column(String(2550))
    

    authors = relationship("Poet",secondary=collection_authors) 
    poems = relationship("CollectionContent",back_populates="collection")

    def __repr__(self) -> str:
        return f"<Collection(title={self.title}>"


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine,expire_on_commit=False) 


