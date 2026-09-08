import json
import os
import re

import cloudscraper
import requests
from bs4 import BeautifulSoup

# Configuración
URL = "https://www.fincaraiz.com.co/arriendo/apartamentos/bogota-dc/el-plan-y-en-mazuren/3-habitaciones/2-banos/desde-2500000/hasta-3500000/m2-desde-70/m2-hasta-110/edificados/incluyendo-expensas?&ordenListado=3&IDmoneda=4"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ARCHIVO_IDS = "inmuebles_vistos.json"


def enviar_telegram(mensaje):
    url_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(
        url_api,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"},
        timeout=30,
    )


def cargar_vistos():
    if os.path.exists(ARCHIVO_IDS):
        with open(ARCHIVO_IDS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_vistos(vistos):
    with open(ARCHIVO_IDS, "w", encoding="utf-8") as f:
        json.dump(vistos, f)


def main():
    # Usamos cloudscraper para imitar un navegador Chrome real y evitar el bloqueo de Cloudflare/Bot
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    respuesta = scraper.get(URL)

    if respuesta.status_code != 200:
        print(f"Error accediendo a Fincaraíz: {respuesta.status_code}")
        return

    soup = BeautifulSoup(respuesta.text, "html.parser")

    # Buscamos todos los links que lleven a un apartamento
    links = soup.find_all("a", href=re.compile(r"/apartamento-en-arriendo-.*?[0-9]+$"))

    vistos = cargar_vistos()
    nuevos_encontrados = False

    for link in links:
        ruta = link["href"]
        id_inmueble = ruta.split("/")[-1]  # Extrae el número final del link
        url_completa = "https://www.fincaraiz.com.co" + ruta

        if id_inmueble not in vistos:
            print(f"¡Nuevo inmueble encontrado! ID: {id_inmueble}")
            mensaje = (
                "🚨 *¡Nuevo Apartamento en Arriendo!*\n\n"
                "📍 Sectores: El Plan / Mazurén\n"
                "Filtros: 3 Hab | 2 Baños | 70-110m2\n\n"
                f"🔗 [Ver el inmueble aquí]({url_completa})"
            )
            enviar_telegram(mensaje)
            vistos.append(id_inmueble)
            nuevos_encontrados = True

    if nuevos_encontrados:
        guardar_vistos(vistos)
    else:
        print("No hay apartamentos nuevos en esta revisión.")


if __name__ == "__main__":
    main()
