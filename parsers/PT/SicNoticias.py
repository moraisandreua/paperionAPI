import requests
from bs4 import BeautifulSoup

class SicNoticias():
    def __init__(self, response) -> None:
        self.response=response

    def fromBreaking(self):
        retorno=[]
        cards = self.response.find("ul", class_="js-list-articles").find_all("li")
        c=0
        for newsCard in cards:
            c+=1
            try:
                link=newsCard.find("article").find("figure").find("a").get("href")
                link="https://sicnoticias.pt"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("article").find("figure").find("a").find("picture").find("img").get("src"),
                    "title":newsCard.find("article").find("div").find("h2").find("a").get_text(),
                    "text":self.getTextFromTitle(link),
                    "website":"SICNOTICIAS"
                }
                retorno.append(noticia)
            except:
                continue
        
        return retorno

    def fromSection(self, section):
        retorno=[]
        
        cards = self.response.find("ul", class_="latest-list").find_all("li")

        for newsCard in cards:
            try:
                link=newsCard.find("article").find("figure").find("a").get("href")
                link="https://sicnoticias.pt"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("article").find("figure").find("a").find("picture").find("img").get("src"),
                    "title":newsCard.find("article").find("div").find("h2").find("a").get_text(),
                    "text":self.getTextFromTitle(link),
                    "website":"SICNOTICIAS"
                }
                retorno.append(noticia)
            except:
                print("        error: error obtaining data from SICNOTICIAS on '"+section+"'")
                continue
        
        return retorno

    def getTextFromTitle(self, url):
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")

        return soup.find("div", class_="item-1 item-1-1 item-odd item-first item-last first CT-html").find("p").find("strong").get_text()