import requests
from bs4 import BeautifulSoup

class DiarioNoticias():
    def __init__(self, response) -> None:
        self.response=response

    def fromBreaking(self):
        retorno=[]
        cards = self.response.find("div", class_="t-sf1-body").find_all("article")
        c=0
        for newsCard in cards:
            try:
                
                link=newsCard.find("header").find("a", class_="t-am-pic").get("href")
                link="https://www.dn.pt"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("header").find("a", class_="t-am-pic").find("figure").find("img").get("src"),
                    "title":newsCard.find("header").find("a", class_="t-am-text").find("h2").find("span").get_text(),
                    "text":self.getTextFromTitle(link),
                    "website":"DIARIONOTICIAS"
                }

                retorno.append(noticia)
                c+=1
            except:
                continue
            
            if c==5:
                break
        
        return retorno

    def fromSection(self, section):
        retorno=[]
        cards = self.response.find("div", class_="t-s11-body").find_all("article", class_="t-s11-am1")
        c=0
        for newsCard in cards:
            try:
                link=newsCard.find("header").find("a", class_="t-am-pic").get("href")
                link="https://www.dn.pt"+link if "https://" not in link else link

                noticia={
                    "link":link,
                    "image":newsCard.find("header").find("a", class_="t-am-pic").find("figure").find("img").get("src"),
                    "title":newsCard.find("header").find("a", class_="t-am-text").find("h2").find("span").get_text(),
                    "text":self.getTextFromTitle(link),
                    "website":"DIARIONOTICIAS"
                }

                retorno.append(noticia)
                c+=1
            except:
                print("        error: error obtaining data from DIARIONOTICIAS on '"+section+"'")
                continue
            
            if c==5:
                break
        
        return retorno

    def getTextFromTitle(self, url):
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")

        return soup.find("div", class_="t-af1-c1-body js-a-content-body-elm-targ js-article-readmore-resize-watch").find("p").get_text()