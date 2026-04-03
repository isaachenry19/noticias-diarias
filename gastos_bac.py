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

meses_es = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']

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
            fecha_str = fecha_match.group(1) if fecha_match else ""
            gastos.append({
                "monto": float(monto_match.group(1).replace(",", "")),
                "comercio": comercio_match.group(1).strip() if comercio_match else "Desconocido",
                "fecha": fecha_str
            })

    mail.logout()
    return gastos

hoy = datetime.now()
ayer = hoy - timedelta(days=1)
es_fin_de_mes = hoy.day == 1
meses_es_nombre = meses_es[ayer.month - 1]

if es_fin_de_mes:
    # Resumen mensual completo
    gastos = leer_emails_bac(dias_atras=31)
    mes_nombre = meses_es[ayer.month - 1].capitalize()
    titulo = f"Cierre de mes BAC - {mes_nombre} {ayer.year}"

    if not gastos:
        mensaje = f"Sin transacciones en {mes_nombre} {ayer.year}."
    else:
        total = sum(g["monto"] for g in gastos)
        comercios = defaultdict(float)
        for g in gastos:
            comercios[g["comercio"]] += g["monto"]
        top3 = sorted(comercios.items(), key=lambda x: x[1], reverse=True)[:3]

        lineas = [
            f"📅 Cierre de {mes_nombre} {ayer.year}",
            f"",
            f"💰 Total del mes: ${total:,.2f}",
            f"🧾 Transacciones: {len(gastos)}",
            f"",
            f"🏆 Top 3 comercios del mes:",
        ]
        medallas = ["🥇", "🥈", "🥉"]
        for i, (comercio, monto) in enumerate(top3):
            lineas.append(f"{medallas[i]} {comercio}: ${monto:,.2f}")

        mensaje = "\n".join(lineas)

else:
    # Gastos de ayer
    gastos_ayer = leer_emails_bac(dias_atras=1)
    
    # Gastos del mes hasta hoy
    dias_del_mes = hoy.day
    gastos_mes = leer_emails_bac(dias_atras=dias_del_mes)
    total_mes = sum(g["monto"] for g in gastos_mes)
    mes_actual = meses_es[hoy.month - 1].capitalize()

    titulo = f"Gastos BAC - ayer {ayer.day} de {meses_es_nombre}"

    if not gastos_ayer:
        lineas = [
            f"📭 Sin transacciones ayer {ayer.day} de {meses_es_nombre}",
            f"",
            f"📊 Lo que llevas gastado en {mes_actual}:",
            f"💳 Acumulado {mes_actual}: ${total_mes:,.2f}",
            f"🧾 Transacciones del mes: {len(gastos_mes)}",
        ]
    else:
        total_ayer = sum(g["monto"] for g in gastos_ayer)
        comercios = defaultdict(float)
        for g in gastos_ayer:
            comercios[g["comercio"]] += g["monto"]
        top3 = sorted(comercios.items(), key=lambda x: x[1], reverse=True)[:3]

        lineas = [
            f"💳 Ayer {ayer.day} de {meses_es_nombre}",
            f"",
            f"💰 Gastado ayer: ${total_ayer:,.2f}",
            f"🧾 Transacciones: {len(gastos_ayer)}",
            f"",
            f"🏆 Top 3 de ayer:",
        ]
        medallas = ["🥇", "🥈", "🥉"]
        for i, (comercio, monto) in enumerate(top3):
            lineas.append(f"{medallas[i]} {comercio}: ${monto:,.2f}")

        lineas += [
            f"",
            f"📊 Como vas en {mes_actual}:",
            f"💳 Acumulado del mes: ${total_mes:,.2f}",
            f"🧾 Total transacciones del mes: {len(gastos_mes)}",
        ]

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
