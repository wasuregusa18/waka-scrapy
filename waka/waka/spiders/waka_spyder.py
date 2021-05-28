
import scrapy
from bs4 import BeautifulSoup, Tag
from collections import defaultdict
import re
from hashlib import md5
from typing import Dict, List, Optional, Tuple



from .shorthand_title_key import conversion_dict
from . import waka_extract_links
from ..orm_parallel import Poet, Poem, Collection, CollectionContent



relative_links = waka_extract_links.link_dict.keys()
absolute_links = ["http://www.asahi-net.or.jp/~sg2h-ymst/yamatouta/"+ link for link in relative_links]
# absolute_links = ["http://www.asahi-net.or.jp/~sg2h-ymst/yamatouta/sennin/narihira.html"]
# from random import sample
# absolute_links = sample(absolute_links,40)
            

END_SECTION_CLASSES = ("song","title","date","link","otitle","title2") #title 2 is for 反歌 etc... 
OTHER_NOTE_CLASSES = ("appre","satyu")
# appre = appreciation, satyu = 左注

class WakaSpider(scrapy.Spider):
    name = "waka"
    allowed_domains = [
        'asahi-net.or.jp'
    ]
    start_urls = absolute_links

    def parse(self, response):
        try:
            soup = BeautifulSoup(response.body.decode('shift-jis'), "lxml") #sometimes jis encoded
        except:
            soup = BeautifulSoup(response.text,"lxml") #sometimes scrapy does a better job

        link = response.url
        rel_link = self.extract_relative_url(link)
        id = self._get_guid(link)

        # author
        author_dict = self.extract_author(soup)
        author_dict["link"] = link
        author_dict["id"] = id
        author_dict["jidai"] = waka_extract_links.link_dict[rel_link]
        yield author_dict

        # poems
        songs = soup.find_all("p",class_=r"song")
        for song in songs:
            poem_dict = self.extract_poem(song)
            poem_dict["link"] = link
            poem_dict["poet_id"] = id
            collection_str = poem_dict.pop("other","") 
            collection_content_list = self.extract_collections(poem_dict,collection_str)
            yield poem_dict
            for collection_content_dict in collection_content_list:
                yield collection_content_dict
        
        # # next page
        # next_page = soup.find("a",text="次の歌人")
        # # should probably regex test right

        # if next_page is not None:
        #     yield response.follow(next_page["href"], callback=self.parse) 

    @staticmethod
    def extract_relative_url(url):
        """extracts relative url from absolute url"""
        return re.search("sennin.*",url)[0]
    
    @staticmethod
    def _get_guid(input:str)->str:
        """Generates an unique identifier for a given item."""
        # hash based solely in the url field
        return md5(input.encode('utf-8')).hexdigest()


    def extract_author(self,soup:BeautifulSoup)->dict:
        """extract author information from beautifulsoup object
        return dict with extracted info"""

        author_dict = defaultdict(lambda: "")
        author_dict["table"] = "poets" #for database schema

        if author_tag:= soup.find("div",class_="header"):
            author_tag = author_tag.text
            name = re.sub("[ \u3000]+"," ",author_tag)
            kanji, hiragana, *other = name.split(" ")

            biography = soup.find("p",class_="biography")
            if biography: biography = biography.text

            author_dict["kanji"] = kanji.strip("\n")
            author_dict["hiragana"] = hiragana
            author_dict["bio"] = biography
            if other: self.extract_suppl_author(author_dict,other)
        
        return author_dict

    def extract_suppl_author(self,author_dict:dict,suppl:list)->None:
        """ updates author_dict with suppl information """
        for ele in suppl:
            # year of birth
            if re.search('.*(?:[1-9]|生没年).*',ele, flags=re.UNICODE): 
                author_dict["dates"] = ele
            # alternate names
            else: 
                author_dict["alias"] += ele


    def extract_poem(self,song:Tag)->dict:
        """extract poem information from beautifulsoup tag object
        return dict with extracted info"""
        
        waka_dict = defaultdict(lambda:"") # sometimes multiple note tags - hence concat to string
        waka_dict["table"] = "poems"
        cleaned_text = re.sub("[ 　]","",song.text)
        waka_dict["poem"] = cleaned_text
        waka_dict["id"] = self._get_guid(cleaned_text)

        if title:= song.find_previous("p",class_=re.compile(".?title")): #sometimes otitle
            is_correct_title = title.find_next("p",class_=re.compile(".?song")) == song
            if is_correct_title:
                title = title.text 
                waka_dict["title"] = title

        analysis = song.find_all_next("p",limit=8)    
        for row in analysis:
            if class_:= row.get("class"):
                class_name = class_[0]
                if class_name in END_SECTION_CLASSES: break
                # elif class_name in OTHER_NOTE_CLASSES: class_name = "note" #will drop this with new schema
                waka_dict[class_name] += row.text
        return waka_dict

    def extract_collections(self,poem_dict:dict, collections_str:str)->List[Dict]:
        """extract collection data from poem_dict - dict is mutated
        returns list of collection content dicts"""
        res = []
        
        # primary collection
        re_poem  = re.compile(r'（(?P<title>[\u4E00-\u9FD0]+)(?P<position>[\d-]*)）$')
        poem_txt = poem_dict["poem"]
        poem_dict["poem"] = re.sub(re_poem,"",poem_txt) #update
        match = re.search(re_poem,poem_txt) #i.e. contains pri collection info
        if match:
            shortened_title, position = match.groups()
            title = self._short2fulltitle(shortened_title)
            # pri_collection = self._get_or_create_collection(title)
            new_collection_content = {
                "table":"collection_contents",
                "poem_id":poem_dict["id"],
                "collection_id":self._get_guid(title),
                "collection_title": title,
                "position":position}
            res.append(new_collection_content)
    
        # other collections
        re_title = re.compile(r'^[\u4E00-\u9FD0の]+(?:\([\u4E00-\u9FD0・]+\))?$') # kanji word or の - with optional bracketed word
        if collections_str:
            cleaned_collections = collections_str.strip("【他出】").split("、") 
            for c in cleaned_collections:
                if re_title.fullmatch(c): #validation
                    collection_content = {
                        "table":"collection_contents",
                        "poem_id":poem_dict["id"],
                        "collection_id":self._get_guid(c),
                        "collection_title": c,
                        "position":""}
                    res.append(collection_content)
        return res
                
        
    def _short2fulltitle(self,short_title:str)->str:
        if long_title:= conversion_dict.get(short_title): #dict of most common
            return long_title
        else: 
            for key in self.seen_collections:
                if key.startswith(short_title): return key #check to see if abbreviation of already seen
        return short_title #give up

    def _get_or_create_collection(self,title:str)->Collection:
        already_seen  = self.seen_collections.get(title)
        if already_seen:
            return already_seen
        else:
            new_collection = self.seen_collections[title] = Collection(title=title)
            return new_collection

        
            
        

