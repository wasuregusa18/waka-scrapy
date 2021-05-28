
import re
from typing import Tuple
import scrapy
from bs4 import BeautifulSoup, Comment
from hashlib import md5

from .kokin_extract_links import full_urls

poem_links = [f"http://www.milord-club.com/Kokin/uta{str(i).zfill(4)}.htm" for i in range(1,1101)]
author_links = full_urls

from random import sample
# author_links = sample(author_links,1)
# poem_links = sample(poem_links,5)
# poem_links = ["http://www.milord-club.com/Kokin/uta0711.htm"]

# # testing
# import requests
# from bs4 import BeautifulSoup
# url = "http://www.milord-club.com/Kokin/uta0400.htm"
# response = requests.get(url)
# response.encoding = "shift-jis"
# soup = BeautifulSoup(response.text,"lxml")

# failed = ['http://www.milord-club.com/Kokin/uta0004.htm',
#  'http://www.milord-club.com/Kokin/uta0036.htm',
#  'http://www.milord-club.com/Kokin/uta0114.htm',
#  'http://www.milord-club.com/Kokin/uta0237.htm',
#  'http://www.milord-club.com/Kokin/uta0298.htm',
#  'http://www.milord-club.com/Kokin/uta0356.htm',
#  'http://www.milord-club.com/Kokin/uta0396.htm',
#  'http://www.milord-club.com/Kokin/uta0398.htm',
#  'http://www.milord-club.com/Kokin/uta0452.htm',
#  'http://www.milord-club.com/Kokin/uta0453.htm',
#  'http://www.milord-club.com/Kokin/uta0457.htm',
#  'http://www.milord-club.com/Kokin/uta0468.htm',
#  'http://www.milord-club.com/Kokin/uta0768.htm',
#  'http://www.milord-club.com/Kokin/uta0779.htm',
#  'http://www.milord-club.com/Kokin/uta0786.htm',
#  'http://www.milord-club.com/Kokin/uta0803.htm',
#  'http://www.milord-club.com/Kokin/uta0875.htm',
#  'http://www.milord-club.com/Kokin/uta0885.htm',
#  'http://www.milord-club.com/Kokin/uta0921.htm',
#  'http://www.milord-club.com/Kokin/uta0924.htm',
#  'http://www.milord-club.com/Kokin/uta1012.htm',
#  'http://www.milord-club.com/Kokin/uta1049.htm']


prefixs_to_drop = set([
    "僧正",
    "僧都",
    "尼",
])

suffixs_to_drop = set([
    "王",
    "法師"
])

special_cases = {
    "雲林院親王":("常康親王","つねやすのみこ"),
    "前太政大臣":("藤原良房","ふじわらのよしふさ"),
    "奈良帝":("平城天皇","へいぜいてんのう"),
    "業平朝臣母":("伊登内親王","いとないしんのう"),
    "二条后": ("藤原高子","ふじわらのたかきこ"),
    "仁和帝":("光孝天皇","こうこうてんのう"),
    "東三条左大臣":("源常","みなもとのときわ"),
    "左大臣": ("藤原時平","ときひら"),
    "良岑宗貞": ("遍照","へんじょう")
}

class KokinSpider(scrapy.Spider):
    name = "kokin"
    allowed_domains = [
        'milord-club.com'
    ]
    start_urls = failed

    def parse(self, response):
        try:
            soup = BeautifulSoup(response.body.decode('shift-jis'), "lxml") #sometimes jis encoded
        except:
            soup = BeautifulSoup(response.text,"lxml") #sometimes scrapy does a better job
        link = response.url
        # yield self.extract_author(soup,link)
        yield self.extract_poem(soup,link)

    @staticmethod
    def _get_guid(input:str)->str:
        """Generates an unique identifier for a given item."""
        # hash based solely in the url field
        return md5(input.encode('utf-8')).hexdigest()

    def extract_author(self,soup:BeautifulSoup,link:str)->dict:
        
        # all hard coded so pretty safe
        kanji = soup.find("td",width=112).text.strip("\xa0")
        hiragana = soup.find("td",width=420).text.strip("\xa0") 
        kanji, hiragana = self.clean_name(kanji,hiragana)
        
        info_section = soup.find("td",width=352)
        dates_grouping = info_section.find_all("font",limit=4)
        dates = self.format_author_dates(dates_grouping)

        bio_text = info_section.find(text=lambda text:isinstance(text,Comment) and text==' 略歴 ').parent.text
        bio = self.format_bio(bio_text)

        #assume that will already have 奈良時代
        author_dict = {
            "table":"poets",
            "id": self._get_guid(kanji),
            "kanji":kanji,
            "hiragana":hiragana,
            "dates":dates,
            "bio":bio,
            "jidai":"平安時代",
            "link":link
        } 

        return author_dict

    def extract_poem(self,soup:BeautifulSoup,link:str)->dict:
        
        # title = soup.find("td", width=400, height=30).text.strip("\xa0")
        # author = soup.find("td", width=140, height=30).text.strip("\xa0")
        *_, title, author = soup.table.tr("td")
        title = title.text.strip("\xa0")
        author = author.text.strip("\xa0")
        author, _ = self.clean_name(author,"")

        poem = soup.find("td", width=542,height=20).text 
        poem = self.strip_whitespace(poem)
        position = soup.find("td", width=36,height=36).text 
        position = self.strip_whitespace(position)
        
        meaning = soup.find('font',class_="char2y").text
        meaning = self.strip_whitespace(meaning)

        if note:= soup.find('ul',type="square"):
            note = note.text #better with formatting
        
        poem_dict = {
            "table":"poems",
            "id": self._get_guid(poem),
            "title":title,
            "poem":poem,
            "poet_id": author, #need to fetch id
            "mean": meaning,
            "note" : note if note else "",
            "link": link,
            "position":position,
            # "collection":"古今和歌集"
        }
        return poem_dict
        
    
    def clean_name(self, kanji:str,hiragana:str)->Tuple[str]:
        if kanji in special_cases:
            return special_cases[kanji]

        for suffix in suffixs_to_drop:
            kanji = re.sub(f"{suffix}$","",kanji)
        for prefix in prefixs_to_drop:
            kanji = re.sub(f"^{prefix}","",kanji)

        hiragana =  re.sub("（.*）","",hiragana)
        return kanji, hiragana

    @staticmethod
    def strip_whitespace(input:str)->str:
        return re.sub(r"[ 　\xa0\n]","",input)


    def format_author_dates(self, dates:list)->str:
        birth,death = [date.text for date in dates[1::2]]
        re_validation = re.compile(r"(?P<west>[\d年不明?]+)(?:（(?P<japan>[\u4E00-\u9FD0]+)）)?")

        def clean_date(date:str):
            temp = re.sub("[\xa0\n 　]","",date)
            return re_validation.search(temp)
        
        temp_birth = re.sub("不明","?（生年未詳）", birth)
        birth_match = clean_date(temp_birth)

        temp_death = re.sub("不明","?（没年未詳）", death)
        death_match = clean_date(temp_death)

        if birth_match["west"] == death_match["west"] == "?": 
            return "生没年未詳"
        return f'{birth_match["japan"]}〜{death_match["japan"]}({birth_match["west"]}-{death_match["west"]})'

    def format_bio(self, bio_text:str)->str:
        start_point = bio_text.find("\n\n\n")
        bio_text = bio_text[start_point:]
        bio_text =  re.sub("[\n 　\xa0]", "", bio_text)
        return re.sub("(\d+番)","古今\g<1>",bio_text)




