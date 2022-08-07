import requests
from bs4 import BeautifulSoup

class CMJornal():
    def __init__(self, response) -> None:
        self.response=response

    def fromBreaking(self):
        retorno=[]
        cards = self.response.find_all("article", class_="destaque")
        for newsCard in cards:
            try:
                link=newsCard.find("div").find("figure").find("a").get("href")
                link="https://sicnoticias.pt/"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("div", class_="figure_container").find("figure").find("a").find("img").get("src"),
                    "title":newsCard.find("div", class_="text_container").find("h2").find("a").get_text(),
                    "text":newsCard.find("div", class_="text_container").find("p").get_text()
                }
                retorno.append(noticia)
            except:
                continue
        
        return retorno

    def fromSection(self, section):
        pass

    def getTextFromTitle(self, url):
        # not needed
        pass