import requests
import json
from bs4 import BeautifulSoup
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector
from flask import Flask
from parsers.PT.CMJornal import CMJornal
from parsers.PT.DiarioNoticias import DiarioNoticias
from parsers.PT.JornalNoticias import JornalNoticias
from parsers.PT.NoticiasAoMinuto import NoticiasAoMinuto
from parsers.PT.SicNoticias import SicNoticias


# URLs to scrap
obj_conf={}

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

def connectDB():
    mydb = mysql.connector.connect(host="localhost", user="root", password="root", database="paperion")
    return mydb

def taskGetBreaking():
    clearOldBreaking()

    for site in urls_breaking:
        req = requests.get(site)
        soup = BeautifulSoup(req.content, "html.parser")
        
        parser=[urls_parser[x] for x in urls_parser if x in site][0]
        parser=parser(soup)
        
        if parser!=None:
            info=parser.fromBreaking()
            for n in info:
                saveNewsInDatabase(n["title"], n["text"], n["image"], n["link"], n["website"], "Breaking", "PT")


def clearOldBreaking():
    mydb=connectDB()
    mycursor = mydb.cursor()

    mycursor.execute("DELETE FROM news WHERE genreId=1")
    mydb.commit()


def saveNewsInDatabase(title, text, image, link, website, genreName, countrySymbol):
    mydb=connectDB()
    mycursor = mydb.cursor()

    sql="INSERT INTO news(image, title, text, link, website, genreId, countryId) values(%s, %s, %s, %s, %s, (SELECT id FROM genre WHERE name LIKE %s LIMIT 1), (SELECT id FROM country WHERE symbol LIKE %s LIMIT 1))"
    params=(image, title, text, link, website, genreName, countrySymbol)
    mycursor.execute(sql, params)
    mydb.commit()


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
    mydb=connectDB()
    mycursor = mydb.cursor()
    
    content_breaking=[]

    sql="SELECT title, text, image, link, website FROM news INNER JOIN genre on genre.id=news.genreId WHERE genre.name=%s"
    params=("Breaking",)
    mycursor.execute(sql, params)
    myresult = mycursor.fetchall()

    for x in myresult:
        content_breaking.append({ "title":x[0], "text":x[1], "image":x[2], "link":x[3], "website":x[4] })

    retornoFiltered=filterGroupByTitle(content_breaking)

    return json.dumps(retornoFiltered, ensure_ascii=False)
    

if __name__ == "__main__":
    f=open("conf.json", "r")
    obj_conf=json.loads(f.read())

    urls_breaking=obj_conf["PT"]["breaking"] # TODO: alterar para aceitar escolha de linguas

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=taskGetBreaking, trigger="interval", seconds=60)
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())

    app.run()