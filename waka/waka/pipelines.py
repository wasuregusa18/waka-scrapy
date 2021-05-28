import re
from .orm_parallel import Session, Poet, Poem, CollectionContent, Collection

import Levenshtein
import pykakasi

# get current collections 
session = Session()
# titles = session.query(Collection.title).all()
# title_set = {t[0] for t in titles}
# poets = session.query(Poet.kanji,Poet.id).all()
kokin = session.query(Collection).filter_by(title="古今和歌集").scalar()
kokin_poems = {re.sub("\(.*\)","",content.poem.poem) :(content.poem,content.poem.poet,content) for content in kokin.poems}
session.close()



class ValidationPipeline:

    def process_item(self, item, spider):
        return item
            
    def validate_data(): 
        kanji_regex = re.compile(r'^[\u4E00-\u9FD0（）]+$')
        hiragana_regex = re.compile(r'^[あ-ん　 ]+$')



class WakaSQLPiline:
    # seen_collections = title_set 

    def process_item(self, item, spider):
        """takes in either Poet, Poem or Collection Content Dict"""
        if new_object:= self.build_object(item):
            session = Session()
            try:
                session.add(new_object) # cascade new collections
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:    
                session.close()
        return item

    def build_object(self,item:dict):
        table = item.pop("table")
        if table == "poets":
            # if item["kanji"] in poets: 
            #     return #already seen
            return Poet(**item)
        elif table == "poems":
            return Poem(**item)
        else: #collection
            title = item.pop("collection_title")
            if title in self.seen_collections: #titles are unique
                return CollectionContent(**item)
            else: #new collection
                self.seen_collections.add(title)
                new_collection = Collection(id=item["collection_id"],title=title) #added on cascade
                return CollectionContent(poem_id=item["poem_id"],collection=new_collection,position=item["position"])

class KokinSQLPipeline:

    def process_item(self, item, spider):
        """takes in either Poet, Poem or Collection Content Dict"""
        session = Session()
        to_add = self.prework_item(item, session)
        # print(to_add)
        try:
            for i in to_add:
                if new_object:= self.build_object(i):
                    session.add(new_object) # cascade new collections
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:    
            session.close()
        return item

    def prework_item(self,item:dict,session)->list: 
        """checks whether poem is unique
        if unique returns [Poem, CollectionContent]
        else updates CollectionContent position"""
        items = []
        unique = self.is_poem_unique(item)
        if unique:
            position = item.pop("position")
            author = session.query(Poet).filter_by(kanji=item["poet_id"]).scalar()
            assert author
            item["poet_id"] = author.id
            items.append(item)
            linking = dict(table="collection_contents",poem_id=item["id"],collection=kokin,position=position)
            items.append(linking)
        return items

    def build_object(self,item:dict):
        table = item.pop("table")
        if table == "poets":
            # if item["kanji"] in poets: 
            #     return #already seen
            return Poet(**item)
        elif table == "poems":
            return Poem(**item)
        else: #collection
            return CollectionContent(**item)
            
    def is_poem_unique(self,poem:dict):
        poem_txt = poem["poem"]
        for p in kokin_poems: #compare to previously scrapped kokin
            close = Levenshtein.ratio(poem_txt,p)
            hira1, hira2 = [self.convert_to_hiragana(i) for i in (poem_txt,p)]
            close_hira = Levenshtein.ratio(hira1,hira2)
            if (close > 0.75 and close_hira > 0.75) or close_hira > 0.9:
                #check same author - abandoned - yombitoshirazu
                seen_author = kokin_poems[p][1].kanji
                scrapped_author = poem["poet_id"]
                # if Levenshtein.ratio(seen_author,scrapped_author) > 0.74:
                #     content = kokin_poems[p][2]
                #     content.position = poem["position"] #session will track change
                print(poem_txt,p,seen_author,scrapped_author)
                return False 
        return True    

    @staticmethod
    def convert_to_hiragana(text:str)->str:
        kks = pykakasi.kakasi()
        res = kks.convert(text)
        return "".join([_["hira"] for _ in res])

                        

# from . import settings
# import mysql.connector
# class MySQLPipeline:
#     """assumes item = {table:table_name, col1_nam:col1_val,}"""
#     mydb = mysql.connector.connect(
#             host=settings.MYSQL_HOST,
#             user=settings.MYSQL_USER,
#             password=settings.MYSQL_PASSWD,
#             database=settings.MYSQL_DBNAME
#         )
#     mycursor = mydb.cursor()

#     def process_item(self, item, spider):

#         #python guarantees .keys() + .values() are same order for subsequent calls
#         table = item.pop("table")
#         format_string = ','.join(['%s'] * len(item))
#         query = f"INSERT INTO {table} ({', '.join(item.keys())}) VALUES({format_string})"

#         self.mycursor.execute(query,tuple(item.values()))
#         self.mydb.commit()
#         return item


