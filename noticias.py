import requests
import os
import feedparser
from datetime import datetime

topic = os.environ.get("NTFY_TOPIC", "noticias-isaac")

# Detectar que notificacion mandar segun la hora
hora = datetime.utcnow().hour

if hora == 14:  # 9am Panama = 14 UTC
    # NOTICIAS GLOBALES
    feed = feedparser.parse("http://feeds.bbci.co.uk/news/world/rss.xml")
    titulo_notif = "Isaac! Aqui tienes las noticias globales del dia"
    noticias = feed.entries[:3]
else:
    # NOTICIAS PANAMA
    feed = feedparser.parse("https://www.laestrella.com.pa/feed")
    titulo_notif = "Isaac! Lo que esta pasando en Panama ahora"
    noticias = feed.entries[:3]

mensaje = "\n\n".join([f"- {n.title}" for n in noticias])

requests.post(
    f"https://ntfy.sh/{topic}",
    data=mensaje.encode("utf-8"),
    headers={
        "Title": titulo_notif,
        "Priority": "default",
        "Tags": "newspaper"
    }
)

print("Notificacion enviada!")
