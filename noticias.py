import requests
import os

topic = os.environ.get("NTFY_TOPIC", "noticias-isaac")

mensaje = requests.get("https://wttr.in/?format=3").text

requests.post(
    f"https://ntfy.sh/{topic}",
    data=mensaje.encode("utf-8"),
    headers={"Title": "Noticia del dia"}
)

print("Notificacion enviada!")
