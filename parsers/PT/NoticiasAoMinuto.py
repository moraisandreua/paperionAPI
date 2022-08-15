import requests
from bs4 import BeautifulSoup

class NoticiasAoMinuto():
    def __init__(self, response) -> None:
        self.response=response

    def fromBreaking(self):
        retorno=[]
        cards = self.response.find_all("div", class_="main-carousel-item-container")
        for newsCard in cards:
            noticia={
                "link":newsCard.find("a").get("href"),
                "image":newsCard.find("a").find("img").get("src"),
                "title":newsCard.find("a").find("div").find("p").get_text(),
                "text":self.getTextFromTitle(newsCard.find("a").get("href")),
                "website":"NOTICIASAOMINUTO"
            }
            retorno.append(noticia)
        
        return retorno

    def fromSection(self, section):
        retorno=[]
        cards = self.response.find_all("div", class_="main-carousel-item-container")
        for newsCard in cards:
            try:
                noticia={
                    "link":newsCard.find("a").get("href"),
                    "image":newsCard.find("a").find("img").get("src"),
                    "title":newsCard.find("a").find("div").find("p").get_text(),
                    "text":self.getTextFromTitle(newsCard.find("a").get("href")),
                    "website":"NOTICIASAOMINUTO"
                }
                retorno.append(noticia)
            except:
                print("        error: error obtaining data from NOTICIASAOMINUTO on '"+section+"'")
                continue
        
        return retorno

    def getTextFromTitle(self, url):
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")

        return soup.find("div", class_="article-excerpt").get_text()