import requests
import json
from bs4 import BeautifulSoup
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector
from flask import Flask, request
from parsers.PT.CMJornal import CMJornal
from parsers.PT.DiarioNoticias import DiarioNoticias
from parsers.PT.JornalNoticias import JornalNoticias
from parsers.PT.NoticiasAoMinuto import NoticiasAoMinuto
from parsers.PT.SicNoticias import SicNoticias
import sys

# to record the errors in other file
#sys.stdout = open('output.txt','w')

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

    print("log: scrapping 'breaking' category")

    for lang in obj_conf:
        urls_breaking=obj_conf[lang]["breaking"]

        for site in urls_breaking:
            req = requests.get(site)
            soup = BeautifulSoup(req.content, "html.parser")
            
            parser=[urls_parser[x] for x in urls_parser if x in site][0]
            parser=parser(soup)
            
            if parser!=None:
                info=parser.fromBreaking()
                for n in info:
                    saveNewsInDatabase(n["title"], n["text"], n["image"], n["link"], n["website"], "Breaking", lang)


def taskGetCategories():
    def scrapWebsiteCategory(requested_website, category, lang):
        print(requested_website)
        req = requests.get(requested_website)
        soup = BeautifulSoup(req.content, "html.parser")

        parser = [urls_parser[wsite] for wsite in urls_parser if wsite in requested_website ][0]
        parser=parser(soup)

        if parser!=None:
            info=parser.fromSection(category)
            for n in info:
                saveNewsInDatabase(n["title"], n["text"], n["image"], n["link"], n["website"], category.capitalize(), lang)

    #scrapWebsiteCategory('https://www.jn.pt/justica.html', 'politics', 'PT')
    for lang in obj_conf:
        for section in obj_conf[lang]:
            time.sleep(5)

            if section=="breaking":
                continue

            print("log: scrapping '"+section+"' category")
            for link in obj_conf[lang][section]:
                scrapWebsiteCategory(link, section, lang)



def clearOldBreaking():
    mydb=connectDB()
    mycursor = mydb.cursor()

    mycursor.execute("DELETE FROM news WHERE genreId=1")
    mydb.commit()


def saveNewsInDatabase(title, text, image, link, website, genreName, countrySymbol):
    mydb=connectDB()
    mycursor = mydb.cursor()

    # ignore the already added news
    sql="SELECT id FROM news WHERE website LIKE %s AND genreId!=(SELECT id FROM genre WHERE name LIKE 'Breaking' LIMIT 1)"
    params=(website,)
    mycursor.execute(sql, params)

    myresult = mycursor.fetchall()
    if len(myresult)>0:
        return True

    # add to database if not in there
    sql="INSERT INTO news(image, title, text, link, website, genreId, countryId) values(%s, %s, %s, %s, %s, (SELECT id FROM genre WHERE name LIKE %s LIMIT 1), (SELECT id FROM country WHERE symbol LIKE %s LIMIT 1))"
    params=(image, title, text, link, website, genreName, countrySymbol)
    mycursor.execute(sql, params)
    mydb.commit()

    return True


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


@app.route("/register", methods=['GET'])
def registerUser():
    pass


@app.route("/shorts", methods=['GET'])
def getShorts():
    pass


@app.route("/newsSeen", methods=['POST'])
def newsSeen():
    pass


@app.route("/newsLike", methods=['POST'])
def newsLike():
    pass


@app.route("/newsSave", methods=['POST'])
def newsSave():
    pass


@app.route("/newsSaved", methods=['GET'])
def getSavedNews():
    pass


@app.route("/newsUnlike", methods=['DELETE'])
def newsUnlike():
    pass


@app.route("/newsUnsave", methods=['DELETE'])
def newsUnsave():
    pass


@app.route("/changeCountry", methods=['PUT'])
def changeCountry():
    pass


@app.route("/deletePref", methods=['DELETE'])
def deletePref():
    pass


@app.route("/news", methods=['GET'])
def getNewsInfo():
    pass


@app.route("/notifications", methods=['GET'])
def getNotifications():
    pass


@app.route("/genre", methods=['GET'])
def getGenreNews():
    mydb=connectDB()
    mycursor = mydb.cursor()

    if "genreId" not in request.args:
        return json.dumps({"status":"error"}, ensure_ascii=False)
    
    genreId = request.args.get('genreId')

    sql="SELECT title, text, image, link, website FROM news WHERE genreId=%s"
    params=(genreId,)

    mycursor.execute(sql, params)
    myresult = mycursor.fetchall()

    retorno=[]
    if len(myresult)>0:
        for n in myresult:
            retorno.append({ "title":n[0], "text":n[1], "image":n[2], "link":n[3], "website":n[4] })

    return json.dumps(retorno, ensure_ascii=False)


@app.route("/genres", methods=['GET'])
def getAllGenres():
    mydb=connectDB()
    mycursor = mydb.cursor()

    sql="SELECT id, name FROM genre"

    mycursor.execute(sql)
    myresult = mycursor.fetchall()

    retorno=[]
    if len(myresult)>0:
        for g in myresult:
            retorno.append({"id":g[0], "name":g[1]})

    return json.dumps(retorno, ensure_ascii=False)


if __name__ == "__main__":
    f=open("conf.json", "r")
    obj_conf=json.loads(f.read())

    #scheduler = BackgroundScheduler()
    #scheduler.add_job(func=taskGetBreaking, trigger="interval", seconds=30)
    #cheduler.add_job(func=taskGetCategories, trigger="interval", seconds=30)
    #scheduler.start()
    taskGetCategories()

    atexit.register(lambda: scheduler.shutdown())

    app.run()