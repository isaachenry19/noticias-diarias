import requests
import os
import feedparser

topic = os.environ.get("NTFY_TOPIC", "noticias-isaac")

# Noticias globales - BBC
feed_global = feedparser.parse("http://feeds.bbci.co.uk/news/world/rss.xml")
noticias_global = "\n".join([f"- {n.title}" for n in feed_global.entries[:3]])

# Noticias Panama - TVN
feed_panama = feedparser.parse("https://www.tvn-2.com/rss/")
noticias_panama = "\n".join([f"- {n.title}" for n in feed_panama.entries[:3]])

mensaje = f"""MUNDO:
{noticias_global}

PANAMA:
{noticias_panama}"""

requests.post(
    f"https://ntfy.sh/{topic}",
    data=mensaje.encode("utf-8"),
    headers={
        "Title": "Isaac! Aqui tienes las noticias del dia",
        "Priority": "default",
        "Tags": "newspaper"
    }
)

print("Notificacion enviada!")
