import requests
import json
from bs4 import BeautifulSoup
from CMJornal import CMJornal
from DiarioNoticias import DiarioNoticias
from JornalNoticias import JornalNoticias
from NoticiasAoMinuto import NoticiasAoMinuto
from SicNoticias import SicNoticias
from flask import Flask

urls_breaking=[ 
    'https://www.noticiasaominuto.com/',
    'https://sicnoticias.pt/ultimas',
    'https://www.cmjornal.pt/exclusivos?ref=CmaoMinuto_DestaquesPrincipais',
    'https://www.dn.pt/ultimas.html',
    'https://www.jn.pt/ultimas.html'
]

urls_politica=[]
urls_sociedade=[]
urls_dinheiro=[] # TODO: adicionar o dinheiro vivo
urls_portugal=[]
urls_mundo=[]
urls_desporto=[]
urls_cultura=[]
urls_viver=[]
urls_tecnologia=[]
urls_fama=[] # TODO: adicionar a revista flash

app = Flask(__name__)

def filterGroupByTitle(news):
    filtered=[]

    for x in news:
        title=[word for word in x["title"].lower().split(" ") if len(word)>4 ]

        howMuchTimesSimilar=0
        for y in filtered:
            
            howMuchTimesInTitle=0
            for word in title:
                if word in y["title"].lower():
                    howMuchTimesInTitle+=1

            if howMuchTimesInTitle>=2:
                y["similar"].append(x)
                howMuchTimesSimilar+=1
        
        if howMuchTimesSimilar==0:
            filtered.append({ "link":x["link"], "image":x["image"], "title":x["title"], "text":x["text"], "website":x["website"], "similar":[] })

    return filtered


@app.route("/breaking")
def breakingNews():
    retornoFiltered=[]

    content_breaking=[]
    for site in urls_breaking:
        req = requests.get(site)
        soup = BeautifulSoup(req.content, "html.parser")
        
        parser=None
        if "noticiasaominuto.com" in site:
            parser=NoticiasAoMinuto(soup)

        if "sicnoticias.pt" in site:
            parser=SicNoticias(soup)

        if "cmjornal.pt" in site:
            parser=CMJornal(soup)

        if "dn.pt" in site:
            parser=DiarioNoticias(soup)

        if "jn.pt" in site:
            parser=JornalNoticias(soup)
        
        if parser!=None:
            content_breaking.extend(parser.fromBreaking())

    retornoFiltered=filterGroupByTitle(content_breaking)

    return json.dumps(retornoFiltered, ensure_ascii=False)

if __name__ == "__main__":
    app.run()