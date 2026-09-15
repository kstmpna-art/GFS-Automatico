#!/usr/bin/env python3
"""Envía por Gmail el GRIB2 más reciente del directorio indicado."""

import argparse
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

LIMITACION_ADJUNTO = 18 * 1024 * 1024  # 18 MB


def obtener_secreto(nombre):
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        raise RuntimeError(f"Falta configurar el secreto {nombre}")
    return valor


def main():
    parser = argparse.ArgumentParser(description="Enviar archivo GRIB por email.")
    parser.add_argument("archivo", type=str, help="Ruta al archivo GRIB2")
    args = parser.parse_args()

    ruta_archivo = Path(args.archivo)

    if not ruta_archivo.is_file():
        raise FileNotFoundError(f"El archivo {ruta_archivo} no existe.")

    mail_user = obtener_secreto("MAIL_USER")
    mail_password = obtener_secreto("MAIL_PASSWORD").replace(" ", "")
    mail_destino_raw = obtener_secreto("MAIL_DESTINO")

    destinatarios = [d.strip() for d in mail_destino_raw.split(",") if d.strip()]

    msg = EmailMessage()
    msg["Subject"] = "Pronóstico GFS Marítimo - Archivo GRIB2"
    msg["From"] = mail_user
    msg["To"] = ", ".join(destinatarios)
    msg.set_content(
        "Hola,\n\nSe adjunta el archivo GRIB2 más reciente con la información meteorológica procesada.\n\nSaludos."
    )

    with open(ruta_archivo, "rb") as f:
        contenido = f.read()

    msg.add_attachment(
        contenido,
        maintype="application",
        subtype="x-grib2",
        filename=ruta_archivo.name,
    )

    contexto = ssl.create_default_context()

    print(f"Iniciando conexión con Gmail para el usuario: {mail_user}")
    print(f"Longitud de la clave leída: {len(mail_password)} caracteres")

    # Conexión mediante STARTTLS (puerto 587)
    with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
        servidor.ehlo()
        servidor.starttls(context=contexto)
        servidor.ehlo()
        servidor.login(mail_user, mail_password)
        servidor.send_message(msg)

    print("¡Correo enviado con éxito!")


if __name__ == "__main__":
    main()
