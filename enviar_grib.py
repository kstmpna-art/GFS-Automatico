#!/usr/bin/env python3
"""Envía por Gmail el GRIB2 más reciente del directorio indicado."""

import argparse
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


LIMITE_ADJUNTO = 18 * 1024 * 1024


def secreto(nombre):
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        raise RuntimeError(f"Falta configurar el secreto {nombre}.")
    return valor


def main():
    parser = argparse.ArgumentParser(description="Envía un GRIB2 mediante Gmail.")
    parser.add_argument("archivo", type=Path)
    args = parser.parse_args()

    archivo = args.archivo
    if not archivo.is_file():
        raise FileNotFoundError(f"No existe el archivo: {archivo}")

    datos = archivo.read_bytes()
    if len(datos) < 16 or not datos.startswith(b"GRIB") or not datos.endswith(b"7777"):
        raise RuntimeError("El archivo no parece ser un GRIB válido y no será enviado.")
    if len(datos) > LIMITE_ADJUNTO:
        raise RuntimeError(
            f"El archivo pesa {len(datos)/(1024*1024):.1f} MiB; "
            "supera el límite seguro de 18 MiB para adjuntarlo por Gmail."
        )

    usuario = secreto("MAIL_USER")
    clave = secreto("MAIL_PASSWORD")
    destino = secreto("MAIL_DESTINO")

    mensaje = EmailMessage()
    mensaje["From"] = usuario
    mensaje["To"] = destino
    mensaje["Subject"] = f"Pronóstico marítimo GFS: {archivo.name}"
    mensaje.set_content(
        "Se adjunta el pronóstico marítimo GFS/GFS-Wave de cinco días, "
        "cada seis horas, listo para abrir en XyGrib.\n\n"
        f"Archivo: {archivo.name}\n"
        f"Tamaño: {len(datos)/(1024*1024):.2f} MiB\n"
    )
    mensaje.add_attachment(
        datos,
        maintype="application",
        subtype="octet-stream",
        filename=archivo.name,
    )

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as servidor:
        servidor.login(usuario, clave)
        servidor.send_message(mensaje)

    print(f"Correo enviado correctamente a {destino}.")


if __name__ == "__main__":
    main()
