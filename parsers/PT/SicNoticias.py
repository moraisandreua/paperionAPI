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
                    "title":newsCard.find("article").find("div", class_="text-details").find("h2").find("a").get_text(),
                    "text":self.getTextFromTitle(link),
                    "website":"SICNOTICIAS"
                }
                retorno.append(noticia)
            except:
                print("    error: error obtaining data from SICNOTICIAS on 'breaking'")
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
                    "title":newsCard.find("article").find("div", class_="text-details").find("h2").find("a").get_text(),
                    "text":self.getTextFromTitle(link),
                    "website":"SICNOTICIAS"
                }
                retorno.append(noticia)
            except:
                print("    error: error obtaining data from SICNOTICIAS on '"+section+"'")
                continue
        
        return retorno

    def getTextFromTitle(self, url):
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")

        if soup.find("div", class_="CT-html").find("p").find("strong"):
            return soup.find("div", class_="CT-html").find("p").find("strong").get_text()
        
        if soup.find("div", class_="g-article-lead lead"):
            return soup.find("div", class_="g-article-lead lead").get_text()
        
        return "Nenhum texto encontrado para este artigo de opinião"