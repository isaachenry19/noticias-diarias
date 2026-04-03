import imaplib
import email
import re
import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "noticias-isaac")

def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                try:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
                except:
                    continue
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
    return body

def leer_emails_bac(dias_atras=1):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_PASS)
    mail.select("inbox")

    fecha_limite = (datetime.now() - timedelta(days=dias_atras)).strftime("%d-%b-%Y")
    _, mensajes = mail.search(None, f'FROM "notificacion_pa@pa.bac.net" SINCE {fecha_limite}')

    gastos = []
    for num in mensajes[0].split():
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        body = get_body(msg)

        comercio_match = re.search(r'Comercio\s*\n?\s*(.+?)(?:\s+USD|\s+\$|\n)', body, re.IGNORECASE)
        monto_match = re.search(r'USD\s*([\d,]+\.?\d*)', body, re.IGNORECASE)
        fecha_match = re.search(r'(\d{4}/\d{2}/\d{2})', body)

        if monto_match:
            gastos.append({
                "monto": float(monto_match.group(1).replace(",", "")),
                "comercio": comercio_match.group(1).strip() if comercio_match else "Desconocido",
                "fecha": fecha_match.group(1) if fecha_match else "Sin fecha"
            })

    mail.logout()
    return gastos

# Detectar si es fin de mes
hoy = datetime.now()
es_fin_de_mes = hoy.day == 1

if es_fin_de_mes:
    # Resumen mensual
    gastos = leer_emails_bac(dias_atras=31)
    mes_anterior = (hoy - timedelta(days=1)).strftime("%B %Y")
    titulo = f"Resumen mensual BAC - {mes_anterior}"
    periodo = f"Todo {mes_anterior}"
else:
    # Resumen del dia anterior
    gastos = leer_emails_bac(dias_atras=1)
    ayer = (hoy - timedelta(days=1))
    meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
    titulo = f"Gastos BAC - ayer {ayer.day} de {meses[ayer.month-1]}"
    periodo = f"Ayer {ayer.day} de {meses[ayer.month-1]} {ayer.year}"

if not gastos:
    mensaje = f"Sin transacciones registradas para {periodo}."
else:
    total = sum(g["monto"] for g in gastos)

    # Top 3 comercios
    comercios = defaultdict(float)
    for g in gastos:
        comercios[g["comercio"]] += g["monto"]
    top3 = sorted(comercios.items(), key=lambda x: x[1], reverse=True)[:3]

    lineas = [
        f"💳 {periodo}",
        f"",
        f"💰 Total gastado: ${total:,.2f}",
        f"🧾 Transacciones: {len(gastos)}",
        f"",
        f"🏆 Top 3 comercios:",
    ]

    medallas = ["🥇", "🥈", "🥉"]
    for i, (comercio, monto) in enumerate(top3):
        lineas.append(f"{medallas[i]} {comercio}: ${monto:,.2f}")

    mensaje = "\n".join(lineas)

requests.post(
    f"https://ntfy.sh/{NTFY_TOPIC}",
    data=mensaje.encode("utf-8"),
    headers={
        "Title": titulo,
        "Priority": "high",
        "Tags": "credit_card,moneybag"
    }
)

print(mensaje)
