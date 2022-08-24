import requests
import json
from bs4 import BeautifulSoup
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector
from flask import Flask, request, Response
from parsers.PT.CMJornal import CMJornal
from parsers.PT.DiarioNoticias import DiarioNoticias
from parsers.PT.JornalNoticias import JornalNoticias
from parsers.PT.NoticiasAoMinuto import NoticiasAoMinuto
from parsers.PT.SicNoticias import SicNoticias
import sys
import secrets

# to record the errors in other file
sys.stdout = open('output.txt','w')

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
    mydb=None

    try:
        mydb = mysql.connector.connect(host="localhost", user="root", password="root", database="paperion")
    except:
        print("Error connecting to database")
    
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
        req = requests.get(requested_website)
        soup = BeautifulSoup(req.content, "html.parser")

        parser = [urls_parser[wsite] for wsite in urls_parser if wsite in requested_website ][0]
        parser=parser(soup)

        if parser!=None:
            info=parser.fromSection(category)
            for n in info:
                saveNewsInDatabase(n["title"], n["text"], n["image"], n["link"], n["website"], category.capitalize(), lang)

    #scrapWebsiteCategory('https://www.noticiasaominuto.com/casa', 'lifestyle', 'PT')
    for lang in obj_conf:
        for section in obj_conf[lang]:
            time.sleep(300)

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
    sql="SELECT id FROM news WHERE link LIKE %s AND genreId!=(SELECT id FROM genre WHERE name LIKE 'Breaking' LIMIT 1)"
    params=(link,)
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

    try:
        sql="SELECT title, text, image, link, website FROM news INNER JOIN genre on genre.id=news.genreId WHERE genre.name=%s"
        params=("Breaking",)
        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        for x in myresult:
            content_breaking.append({ "title":x[0], "text":x[1], "image":x[2], "link":x[3], "website":x[4] })
    except:
        print("Error on '/breaking' searching for news ")

    retornoFiltered=filterGroupByTitle(content_breaking)

    return Response(json.dumps(retornoFiltered, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/register", methods=['GET'])
def registerUser():
    if "countryId" not in request.args:
        return Response(json.dumps({"status":"O parâmetro 'countryId' é obtrigatório"}, ensure_ascii=False), status=400, mimetype='application/json')

    mydb=connectDB()
    mycursor = mydb.cursor()

    countryId=request.args.get("countryId")
    authToken=""

    # check if there is a user with this token
    try:
        myresult=[0]
        while len(myresult)>0:
            authToken=secrets.token_hex(16)

            sql="SELECT id FROM user WHERE auth_token=%s"
            params=(authToken,)
            mycursor.execute(sql, params)
            myresult = mycursor.fetchall()
    except:
        print("Error on /register, getting an unique token")
        return Response(json.dumps({"status":"Erro ao encontrar um token para o utilizador"}, ensure_ascii=False), status=500, mimetype='application/json')

    # add new user
    try:
        sql="INSERT INTO user(countryId, auth_token) VALUES(%s, %s)"
        params=(countryId, authToken)

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /register, inserting new user")
        return Response(json.dumps({"status":"Erro ao adicionar o utilizador à BD"}, ensure_ascii=False), status=500, mimetype='application/json')

    # return authToken
    return Response(json.dumps({"auth_token":authToken}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/shorts", methods=['GET'])
def getShorts():
    if "auth_token" not in request.args:
        return Response(json.dumps({"status":"O parâmetro 'auth_token' é obtrigatório"}, ensure_ascii=False), status=401, mimetype='application/json')

    auth_token=request.args.get("auth_token")

    try:
        sql="SELECT news.genreId, count(news.id) AS pref FROM liked INNER JOIN news ON news.id=liked.newsId INNER JOIN user ON user.id=liked.userId WHERE user.auth_token=%s GROUP BY news.genreId ORDER BY pref DESC;"
        params=(auth_token,)

        # TODO: test this after everything else working
    except:
        print("Error on /shorts, searching for short news")
        return Response(json.dumps({"status":"Erro ao pesquisar por short news"}, ensure_ascii=False), status=500, mimetype='application/json')

    # TODO: return of short news


@app.route("/newsSeen", methods=['POST'])
def newsSeen():
    postRequest = request.get_json()

    if "auth_token" not in postRequest or "newsId" not in postRequest:
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'newsId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')
    
    auth_token=postRequest["auth_token"]
    newsId=postRequest["newsId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    # check if the user already saw it
    try:
        sql="SELECT * FROM newsView WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1) AND newsId=%s"
        params=(auth_token,newsId)

        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        if len(myresult)>0:
            return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')
    except:
        print("Error on /newsSeen, checking if user already saw the news")
        return Response(json.dumps({"status":"Erro ao verificar se o utilizador já viu a notifica"}, ensure_ascii=False), status=500, mimetype='application/json')

    # insert 'view' in db
    try:
        sql="INSERT INTO newsView(userId, newsId) VALUES((SELECT id FROM user WHERE auth_token=%s LIMIT 1), %s)"

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /newsSeen, inserting view in database")
        return Response(json.dumps({"status":"Erro ao inserir 'view' na base de dados"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/newsLike", methods=['POST'])
def newsLike():
    postRequest = request.get_json()

    if "auth_token" not in postRequest or "newsId" not in postRequest:
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'newsId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')
    
    auth_token=postRequest["auth_token"]
    newsId=postRequest["newsId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    # check if the user already liked it
    try:
        sql="SELECT * FROM liked WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1) AND newsId=%s"
        params=(auth_token,newsId)

        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        if len(myresult)>0:
            return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')
    except:
        print("Error on /newsLike, checking if user already liked the news")
        return Response(json.dumps({"status":"Erro ao verificar se o utilizador já gostou da noticia antes"}, ensure_ascii=False), status=500, mimetype='application/json')

    # insert like in db
    try:
        sql="INSERT INTO liked(userId, newsId) VALUES((SELECT id FROM user WHERE auth_token=%s LIMIT 1), %s)"

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /newsLike, inserting like ")
        return Response(json.dumps({"status":"Erro ao inserir like na base"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/newsSave", methods=['POST'])
def newsSave():
    postRequest = request.get_json()

    if "auth_token" not in postRequest or "newsId" not in postRequest:
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'newsId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')
    
    auth_token=postRequest["auth_token"]
    newsId=postRequest["newsId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    # check if the user already liked it
    try:
        sql="SELECT * FROM saved WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1) AND newsId=%s"
        params=(auth_token,newsId)

        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        if len(myresult)>0:
            return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')
    except:
        print("Error on /newsSave, checking if user already liked it")
        return Response(json.dumps({"status":"Erro ao verificar se o utilizador já guardou a noticia"}, ensure_ascii=False), status=500, mimetype='application/json')

    # insert like in db
    try:
        sql="INSERT INTO saved(userId, newsId) VALUES((SELECT id FROM user WHERE auth_token=%s LIMIT 1), %s)"

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /newsSave, inserting a 'save' in db")
        return Response(json.dumps({"status":"Erro ao guardar a notícia"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/newsSaved", methods=['GET'])
def getSavedNews():
    if "auth_token" not in request.args:
        return Response(json.dumps({"status":"O parâmetro 'auth_token' é obrigatório"}, ensure_ascii=False), status=401, mimetype='application/json')

    auth_token=request.args.get("auth_token")

    mydb=connectDB()
    mycursor = mydb.cursor()
    
    retorno=[]
    try:
        sql="SELECT news.id, news.title, news.text, news.link, news.website, news.genreId, genre.name FROM saved INNER JOIN news ON saved.newsId=news.id INNER JOIN genre ON genre.id=news.genreId WHERE saved.userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1)"
        params=(auth_token,)

        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        for n in myresult:
            retorno.append({
                "id":n[0],
                "title":n[1],
                "text":n[2],
                "link":n[3],
                "website":n[4],
                "genreId":n[5],
                "genreName":n[6],
            })
    except:
        print("Error on /newsSaved, searching for user's saved news")
        return Response(json.dumps({"status":"Erro ao pesquisar pelas noticias guardadas do utilizador"}, ensure_ascii=False), status=500, mimetype='application/json')
    
    return Response(json.dumps({"news":retorno}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/newsUnlike", methods=['DELETE'])
def newsUnlike():
    if "auth_token" not in request.get_json() or "newsId" not in request.get_json():
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'newsId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')

    payload=request.get_json()
    auth_token=payload["auth_token"]
    newsId=payload["newsId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    try:
        sql="DELETE FROM liked WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1) AND newsId=%s"
        params=(auth_token,newsId)

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /newsUnlike, deleting like from database")
        return Response(json.dumps({"status":"Erro ao eliminar like da base de dados"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')

    
@app.route("/newsUnsave", methods=['DELETE'])
def newsUnsave():
    if "auth_token" not in request.get_json() or "newsId" not in request.get_json():
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'newsId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')

    payload=request.get_json()
    auth_token=payload["auth_token"]
    newsId=payload["newsId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    try:
        sql="DELETE FROM saved WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1) AND newsId=%s"
        params=(auth_token,newsId)

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /newsUnsave, deleting 'save' from database")
        return Response(json.dumps({"status":"Erro ao eliminar 'save' da base de dados"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/changeCountry", methods=['PUT'])
def changeCountry():
    if "auth_token" not in request.get_json() or "countryId" not in request.get_json():
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'countryId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')

    payload=request.get_json()
    auth_token=payload["auth_token"]
    countryId=payload["countryId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    try:
        sql="UPDATE user SET countryId=%s WHERE auth_token=%s"
        params=(countryId, auth_token)

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /changeCountry, updating country in database")
        return Response(json.dumps({"status":"Erro ao atualizar o pais do utilizador base de dados"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/deletePref", methods=['DELETE'])
def deletePref():
    if "auth_token" not in request.get_json():
        return Response(json.dumps({"status":"O parâmetro 'auth_token' é obrigatório"}, ensure_ascii=False), status=401, mimetype='application/json')

    payload=request.get_json()
    auth_token=payload["auth_token"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    try:
        sql="DELETE FROM liked WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1)"
        params=(auth_token,)

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /deletePref, deleting all user likes from database")
        return Response(json.dumps({"status":"Erro ao eliminar o registo de likes do utilizador"}, ensure_ascii=False), status=500, mimetype='application/json')

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/news", methods=['GET'])
def getNewsInfo():
    pass


@app.route("/notifications", methods=['GET'])
def getNotifications():
    if "auth_token" not in request.get_json():
        return Response(json.dumps({"status":"O parâmetro 'auth_token' é obrigatório"}, ensure_ascii=False), status=401, mimetype='application/json')

    payload=request.get_json()
    auth_token=payload["auth_token"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    retorno=[]
    try:
        sql="SELECT news.id, news.title, news.text, news.link, news.website, news.genreId, genre.name FROM notification INNER JOIN news ON notification.newsId=news.id INNER JOIN genre ON genre.id=news.genreId WHERE notification.userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1)"
        params=(auth_token,)

        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        for n in myresult:
            retorno.append({
                "id":n[0],
                "title":n[1],
                "text":n[2],
                "link":n[3],
                "website":n[4],
                "genreId":n[5],
                "genreName":n[6],
            })
    except:
        print("Error on /notifications, searching for user's notifications")
        return Response(json.dumps({"status":"Erro ao pesquisar as notificações para o utilizador"}, ensure_ascii=False), status=500, mimetype='application/json')    
    
    return Response(json.dumps({"news":retorno}, ensure_ascii=False), status=200, mimetype='application/json')


@app.route("/notifications", methods=['DELETE'])
def deleteNotification():
    if "auth_token" not in request.get_json() or "newsId" not in request.get_json():
        return Response(json.dumps({"status":"Os parâmetros 'auth_token' e 'newsId' são obrigatórios"}, ensure_ascii=False), status=401, mimetype='application/json')

    payload=request.get_json()
    auth_token=payload["auth_token"]
    newsId=payload["newsId"]

    mydb=connectDB()
    mycursor = mydb.cursor()

    try:
        sql="DELETE FROM notification WHERE userId=(SELECT id FROM user WHERE auth_token=%s LIMIT 1) AND newsId=%s"
        params=(auth_token,newsId)

        mycursor.execute(sql, params)
        mydb.commit()
    except:
        print("Error on /notifications, deleting a user notification")
        return Response(json.dumps({"status":"Erro ao eliminar um notificação do utilizador"}, ensure_ascii=False), status=500, mimetype='application/json') 

    return Response(json.dumps({"status":"success"}, ensure_ascii=False), status=200, mimetype='application/json')        


@app.route("/genre", methods=['GET'])
def getGenreNews():
    if "genreId" not in request.args:
        return Response(json.dumps({"status":"O parâmetro 'genreId' é obrigatório"}, ensure_ascii=False), status=401, mimetype='application/json')
    
    mydb=connectDB()
    mycursor = mydb.cursor()
    genreId = request.args.get('genreId')

    retorno=[]
    try:
        sql="SELECT title, text, image, link, website FROM news WHERE genreId=%s"
        params=(genreId,)

        mycursor.execute(sql, params)
        myresult = mycursor.fetchall()

        if len(myresult)>0:
            for n in myresult:
                retorno.append({ "title":n[0], "text":n[1], "image":n[2], "link":n[3], "website":n[4] })
    except:
        print("Error on /genre, searching for genre's news")
        return Response(json.dumps({"status":"Erro ao pesquisar as notícias de uma categoria"}, ensure_ascii=False), status=500, mimetype='application/json') 

    return Response(json.dumps({"news":retorno}, ensure_ascii=False), status=200, mimetype='application/json')     


@app.route("/genres", methods=['GET'])
def getAllGenres():
    mydb=connectDB()
    mycursor = mydb.cursor()

    try:
        sql="SELECT id, name FROM genre"

        mycursor.execute(sql)
        myresult = mycursor.fetchall()

        retorno=[]
        if len(myresult)>0:
            for g in myresult:
                retorno.append({"id":g[0], "name":g[1]})
    except:
        print("Error on /genres, searching for all genres")
        return Response(json.dumps({"status":"Erro ao pesquisar por todas as categorias"}, ensure_ascii=False), status=500, mimetype='application/json') 

    return Response(json.dumps({"genres":retorno}, ensure_ascii=False), status=200, mimetype='application/json')    


if __name__ == "__main__":
    f=open("conf.json", "r")
    obj_conf=json.loads(f.read())

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=taskGetBreaking, trigger="interval", seconds=3600)
    scheduler.add_job(func=taskGetCategories, trigger="interval", seconds=3600)
    scheduler.start()
    #taskGetCategories()

    atexit.register(lambda: scheduler.shutdown())

    app.run()