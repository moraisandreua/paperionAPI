import requests
import json
from bs4 import BeautifulSoup
from CMJornal import CMJornal
from DiarioNoticias import DiarioNoticias
from JornalNoticias import JornalNoticias
from NoticiasAoMinuto import NoticiasAoMinuto
from SicNoticias import SicNoticias

urls_breaking=[
    #'https://www.noticiasaominuto.com/',
    #'https://sicnoticias.pt/ultimas',
    #'https://www.cmjornal.pt/exclusivos?ref=CmaoMinuto_DestaquesPrincipais',
    #'https://www.dn.pt/ultimas.html',
    'https://www.jn.pt/ultimas.html'
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

    if "dn.pt" in site:
        parser=DiarioNoticias(soup)

    if "jn.pt" in site:
        parser=JornalNoticias(soup)
    
    if parser!=None:
        content_breaking=parser.fromBreaking()

f=open("quotes.json", "w")
f.write(json.dumps(content_breaking, ensure_ascii=False))