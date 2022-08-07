import requests
import json
from bs4 import BeautifulSoup
from NoticiasAoMinuto import NoticiasAoMinuto

urls_breaking=[
    'https://www.noticiasaominuto.com/'
]

content_breaking=[]

for site in urls_breaking:
    req = requests.get(site)
    soup = BeautifulSoup(req.content, "html.parser")
    
    parser=None
    if "noticiasaominuto.com" in site:
        parser=NoticiasAoMinuto(soup)
    
    if parser!=None:
        content_breaking=parser.fromBreaking()

f=open("quotes.json", "w")
f.write(json.dumps(content_breaking, ensure_ascii=False))