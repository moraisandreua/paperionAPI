import requests
import json
from bs4 import BeautifulSoup
from CMJornal import CMJornal
from NoticiasAoMinuto import NoticiasAoMinuto
from SicNoticias import SicNoticias

urls_breaking=[
    #'https://www.noticiasaominuto.com/',
    #'https://sicnoticias.pt/ultimas',
    'https://www.cmjornal.pt/exclusivos?ref=CmaoMinuto_DestaquesPrincipais'
]

content_breaking=[]

for site in urls_breaking:
    req = requests.get(site)
    soup = BeautifulSoup(req.content, "html.parser")
    
    parser=None
    if "noticiasaominuto.com" in site:
        parser=NoticiasAoMinuto(soup)

    if "sicnoticias.pt" in site:
        parser=SicNoticias(soup)

    if "cmjornal.pt" in site:
        parser=CMJornal(soup)
    
    if parser!=None:
        content_breaking=parser.fromBreaking()

f=open("quotes.json", "w")
f.write(json.dumps(content_breaking, ensure_ascii=False))