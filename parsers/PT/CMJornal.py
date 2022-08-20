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
                link="https://cmjornal.pt"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("div", class_="figure_container").find("figure").find("a").find("img").get("src"),
                    "title":newsCard.find("div", class_="text_container").find("h2").find("a").get_text(),
                    "text":newsCard.find("div", class_="text_container").find("p").get_text(),
                    "website":"CMJORNAL"
                }
                retorno.append(noticia)
            except:
                continue
        
        return retorno

    def fromSection(self, section):
        retorno=[]
        cards = self.response.findAll("article", class_="destaque")[0:7]

        for newsCard in cards:
            try:
                link=newsCard.find("div", class_="figure_container").find("figure").find("a").get("href")
                link="https://cmjornal.pt"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("div", class_="figure_container").find("figure").findAll("a")[-1].find("img").get("src"), # there are some times that the image has de indicator of video existance. in that case, the image is inside the second <a>
                    "title":newsCard.find("div", class_="text_container").find("h2").find("a").get_text(),
                    "text":newsCard.find("div", class_="text_container").find("p").get_text(),
                    "website":"CMJORNAL"
                }
                
                retorno.append(noticia)
            except:
                print("        error: error obtaining data from CMJORNAL on '"+section+"'")
                continue
        
        return retorno

    def getTextFromTitle(self, url):
        # not needed
        pass