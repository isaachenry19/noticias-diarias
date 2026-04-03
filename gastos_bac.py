import imaplib
import email
import re
import os
import requests
from datetime import datetime, timedelta

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "noticias-isaac")

def leer_emails_bac():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_PASS)
    mail.select("inbox")

    fecha_limite = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
    _, mensajes = mail.search(None, f'FROM "notificacion_pa@pa.bac.net" SINCE {fecha_limite}')

    gastos = []
    for num in mensajes[0].split():
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        monto = re.search(r'\$\s*([\d,]+\.?\d*)', body)
        comercio = re.search(r'(?:en|at|comercio|merchant)[:\s]+([^\n\r]+)', body, re.IGNORECASE)
        
        if monto:
            gastos.append({
                "monto": float(monto.group(1).replace(",", "")),
                "comercio": comercio.group(1).strip() if comercio else "Desconocido"
            })

    mail.logout()
    return gastos

def categorizar(comercio):
    comercio = comercio.lower()
    if any(x in comercio for x in ["restaurant", "food", "pizza", "sushi", "cafe", "coffee"]):
        return "Comida"
    elif any(x in comercio for x in ["uber", "taxi", "gasolina", "gas", "parking"]):
        return "Transporte"
    elif any(x in comercio for x in ["amazon", "apple", "netflix", "spotify", "google"]):
        return "Suscripciones"
    elif any(x in comercio for x in ["farmacia", "pharmacy", "medic", "salud"]):
        return "Salud"
    elif any(x in comercio for x in ["super", "market", "rey", "riba smith", "xtra"]):
        return "Supermercado"
    else:
        return "Otros"

gastos = leer_emails_bac()

if not gastos:
    mensaje = "No se encontraron gastos del BAC en los ultimos 30 dias."
else:
    total = sum(g["monto"] for g in gastos)
    
    categorias = {}
    for g in gastos:
        cat = categorizar(g["comercio"])
        categorias[cat] = categorias.get(cat, 0) + g["monto"]

    lineas = [f"RESUMEN BAC — ultimos 30 dias", f"Total gastado: ${total:,.2f}", ""]
    for cat, monto in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        lineas.append(f"{cat}: ${monto:,.2f}")
    
    lineas.append("")
    lineas.append(f"Total transacciones: {len(gastos)}")
    mensaje = "\n".join(lineas)

requests.post(
    f"https://ntfy.sh/{NTFY_TOPIC}",
    data=mensaje.encode("utf-8"),
    headers={
        "Title": "Isaac! Aqui van tus gastos del BAC",
        "Priority": "default",
        "Tags": "credit_card"
    }
)

print(mensaje)
