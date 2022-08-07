import requests
from bs4 import BeautifulSoup

class JornalNoticias():
    def __init__(self, response) -> None:
        self.response=response

    def fromBreaking(self):
        retorno=[]
        cards = self.response.find_all("article", class_="t-g1-l4-am1")
        for newsCard in cards:
            try:
                link=newsCard.find("header").find("figure").find("a").get("href")
                link="https://www.jn.pt"+link if "https://" not in link else link
                noticia={
                    "link":link,
                    "image":newsCard.find("header").find("figure").find("a").find("picture").find("img").get("data-src"),
                    "title":newsCard.find("header").find("h2").find("a").get_text(),
                    "text":self.getTextFromTitle(link)
                }

                retorno.append(noticia)
            except:
                continue
        
        return retorno

    def fromSection(self, section):
        pass

    def getTextFromTitle(self, url):
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")
        return soup.find("p", class_="t-article-content-intro-1").find("strong").get_text()