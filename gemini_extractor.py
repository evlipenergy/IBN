import json
import re
from PIL import Image

EXTRACTION_PROMPT = """
Du siehst ein oder mehrere Fotos von Typenschildern von Heizungskomponenten (Wärmepumpen, Speicher, Hydraulikstationen).

Extrahiere für jedes erkennbare Gerät:
- Hersteller
- Modellbezeichnung / Typ (exakt wie auf dem Schild)
- Seriennummer (exakt, Buchstaben und Zahlen)
- Leistung (kW) falls sichtbar
- Baujahr falls sichtbar

Antworte als JSON-Array. Beispiel:
[
  {
    "hersteller": "Vaillant",
    "modell": "aroTHERM plus VWL 75/8.1 A 230V",
    "seriennummer": "21261080000337113133876719N0",
    "leistung_kw": "3.5",
    "baujahr": null
  }
]

Wenn ein Feld nicht erkennbar ist, setze null. Gib NUR das JSON zurück, keinen anderen Text.
"""


def extract_from_pil_images(images: list, api_key: str) -> list:
    """Erwartet eine Liste von PIL.Image-Objekten."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    response = model.generate_content([EXTRACTION_PROMPT] + images)

    text = response.text.strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []
