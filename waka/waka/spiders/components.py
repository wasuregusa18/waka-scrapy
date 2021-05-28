
# from bs4 import BeautifulSoup
# from re import compile
# import re
# from collections import defaultdict
# import requests

# # path = "sample.html"
# path = "narihira.html"
# with open(path,"r") as file:
#     soup = BeautifulSoup(file, features="lxml")

# # path = "http://www.asahi-net.or.jp/~sg2h-ymst/yamatouta/sennin/izutari.html"
# # html = requests.get(path).text
# # soup = BeautifulSoup(html)

# author_tag = soup.find("div",class_="header").text
# name, *other = author_tag.split("\u3000") #other usually has dates where avaliable + other names
# kanji, hiragana = name.split("  ") # two spaces
# biography = soup.find("p",class_="biography").text


# author_dict = defaultdict(lambda:"")
# author_dict["kanji"] = kanji.strip("\n")
# author_dict["hiragana"] = hiragana
# author_dict["biography"] = biography

# if other:
#     for ele in other:
#         if re.search('.*(?:[1-9]|生没年).*',ele, flags=re.UNICODE): # means year of birth info
#             author_dict["dates"] = ele
#         else: #means other name info
#             author_dict["alias"] += ele









# END_SECTION_CLASSES = ("title","date","link")

# songs = soup.find_all("p",class_=r"song")
# for song in songs:
#     waka_dict = defaultdict(lambda:"")
#     title = song.find_previous("p",class_=compile(".?title")).text
#     analysis = song.find_all_next("p",limit=8)
    
#     waka_dict["title"] = title
#     waka_dict["song"] = song.text
#     waka_dict["author"] = author_dict["kanji"] #ideally want a foreign key here

#     for row in analysis:
#         class_ = row["class"][0]
#         if class_ in END_SECTION_CLASSES: break
#         else:
#             waka_dict[class_] += row.text


        
# # basically have everything just need to sort out note into individual groups
# # but do that in pipeline 


#     meaning = song.find("p",class_="mean")
#     notes = song.find_all("p",class_="note")
#     sources = song.find("p",class_="other")
#     hasei = song.find("p",class_="hasei") #may search through 
#     honka = song.find("p",class_="honka")

# # title always included in html even when empty
# # note, honka, hasei, other, mean
# # should I pipeline out the notes - 
# # I see 語釈・補記・ゆかりの地
# # maybe I should use the japense names 
# # wouldn't it be interesting to be able to search by ゆかりのち

# #can have multiple notes - should I combine them all


