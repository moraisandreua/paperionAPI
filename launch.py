import requests
import json
from bs4 import BeautifulSoup
from parsers.PT.CMJornal import CMJornal
from parsers.PT.DiarioNoticias import DiarioNoticias
from parsers.PT.JornalNoticias import JornalNoticias
from parsers.PT.NoticiasAoMinuto import NoticiasAoMinuto
from parsers.PT.SicNoticias import SicNoticias
from flask import Flask

# URLs to scrap
urls_breaking=[]
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

# dictionary to match URL to PARSER
urls_parser={
    "noticiasaominuto.com":NoticiasAoMinuto,
    "sicnoticias.pt":SicNoticias,
    "cmjornal.pt":CMJornal,
    "dn.pt":DiarioNoticias,
    "jn.pt":JornalNoticias
}

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
        
        parser=[urls_parser[x] for x in urls_parser if x in site][0]
        parser=parser(soup)
        
        if parser!=None:
            content_breaking.extend(parser.fromBreaking())

    retornoFiltered=filterGroupByTitle(content_breaking)

    return json.dumps(retornoFiltered, ensure_ascii=False)

if __name__ == "__main__":
    f=open("conf.json", "r")
    obj_conf=json.loads(f.read())

    urls_breaking=obj_conf["PT"]["breaking"] # TODO: alterar para aceitar escolha de linguas

    app.run()