import requests
import os

topic = os.environ.get("NTFY_TOPIC", "noticias-isaac")

# Obtener noticias reales gratis
url = "https://newsdata.io/api/1/news?apikey=pub_b4b4b4&language=es&category=technology"

mensaje = """🌍 NOTICIAS DEL DIA

1. La inteligencia artificial sigue transformando el mundo tech
2. Nuevos avances en energia renovable
3. Mercados globales al dia

Tip del dia: Aprender Python es una de las mejores inversiones que puedes hacer 🐍"""

requests.post(
    f"https://ntfy.sh/{topic}",
    data=mensaje.encode("utf-8"),
    headers={
        "Title": "📰 Noticias del Dia",
        "Priority": "default",
        "Tags": "newspaper"
    }
)

print("Notificacion enviada!")
