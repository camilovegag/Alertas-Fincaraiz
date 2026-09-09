import os
import json
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
    requests.post(url_api, data={
        'chat_id': TELEGRAM_CHAT_ID, 
        'text': mensaje, 
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    })

def cargar_vistos():
    if os.path.exists(ARCHIVO_IDS):
        with open(ARCHIVO_IDS, "r") as f:
            return json.load(f)
    return []

def guardar_vistos(vistos):
    with open(ARCHIVO_IDS, "w") as f:
        json.dump(vistos, f)

def main():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    respuesta = scraper.get(URL)

    if respuesta.status_code != 200:
        print(f"Error accediendo a Fincaraíz: {respuesta.status_code}")
        return

    soup = BeautifulSoup(respuesta.text, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'/apartamento-en-arriendo-.*?[0-9]+$'))
    
    vistos = cargar_vistos()
    nuevos_encontrados = False

    for link in links:
        ruta = link.get('href', '')
        id_inmueble = ruta.split('/')[-1]
        url_completa = "https://www.fincaraiz.com.co" + ruta

        if id_inmueble not in vistos:
            # Buscar el contenedor padre de la tarjeta del inmueble
            tarjeta = link.find_parent('div') or link
            texto_tarjeta = tarjeta.get_text(" ", strip=True)

            # 1. Extraer Precio
            precio_match = re.search(r'\$\s*[\d\.]+(?:\s*\+\s*\$\s*[\d\.]+\s*admin)?', texto_tarjeta)
            precio = precio_match.group(0) if precio_match else "Consultar precio"

            # 2. Extraer Título o ubicación
            strong_tag = tarjeta.find('strong') or tarjeta.find('h2')
            titulo = strong_tag.get_text(strip=True) if strong_tag else "Apartamento en Arriendo"

            # 3. Extraer Metros Cuadrados, Habitaciones y Baños
            area_match = re.search(r'\d+\s*m²', texto_tarjeta, re.IGNORECASE)
            habs_match = re.search(r'\d+\s*Habs\.?', texto_tarjeta, re.IGNORECASE)
            banos_match = re.search(r'\d+\s*Baños', texto_tarjeta, re.IGNORECASE)

            area = area_match.group(0) if area_match else "N/A m²"
            habs = habs_match.group(0) if habs_match else "3 Habs."
            banos = banos_match.group(0) if banos_match else "2 Baños"

            # Armar mensaje personalizado
            mensaje = (
                f"🚨 *¡Nuevo Apartamento Encontrado!*\n\n"
                f"📍 *{titulo}*\n"
                f"💰 *Precio:* `{precio}`\n"
                f"📐 *Detalles:* {area} • {habs} • {banos}\n\n"
                f"🔗 [Ver oferta en Fincaraíz]({url_completa})"
            )

            print(f"Enviando notificación para ID: {id_inmueble}")
            enviar_telegram(mensaje)
            vistos.append(id_inmueble)
            nuevos_encontrados = True

    if nuevos_encontrados:
        guardar_vistos(vistos)
    else:
        print("No hay apartamentos nuevos en esta revisión.")

if __name__ == "__main__":
    main()
