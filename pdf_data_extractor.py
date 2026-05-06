"""
Extrahiert Kundendaten aus VAMO-Projektdokumenten (PDF) via Gemini.
PDFs werden direkt an Gemini übergeben (kein pypdf-Textumweg).
"""
import json
import re
import base64
import tempfile
import os


EXTRACTION_PROMPT = """
Du bekommst ein oder mehrere VAMO-Projektdokumente (Baustellenablaufplan, Hydraulikschema, Einstellwerte).

Extrahiere folgende Informationen soweit vorhanden:

Aus dem Baustellenablaufplan:
- projektnummer: Projektnummer (z.B. C-2508-0023379-01)
- kunde_nachname: Nachname des Kunden (Feld "Kunde")
- adresse_komplett: Vollständige Adresse aus dem Feld "Adresse" (z.B. "Brunnenstraße 1, 17391 Krien, DE")
- anlage_strasse: Straßenname ohne Hausnummer
- anlage_hausnr: Hausnummer
- anlage_plz: PLZ (5-stellig)
- anlage_ort: Ort
- telefon: Telefonnummer
- wp_modell: Wärmepumpenmodell (z.B. "aroTHERM plus VWL 55/8.1 A")

Aus den Einstellwerten:
- hydraulikplan_nr: Hydraulikplan-Nummer
- at_abschaltgrenze: AT-Abschaltgrenze (typisch: 17)
- heizkurve: Heizkurvensteigung (z.B. 1,1)

Antworte NUR als JSON. Felder die nicht gefunden werden auf null setzen.
Beispiel:
{
  "projektnummer": "C-2508-0023379-01",
  "kunde_nachname": "Schäfer",
  "adresse_komplett": "Brunnenstraße 1, 17391 Krien, DE",
  "anlage_strasse": "Brunnenstraße",
  "anlage_hausnr": "1",
  "anlage_plz": "17391",
  "anlage_ort": "Krien",
  "telefon": "+4917661343708",
  "wp_modell": "aroTHERM plus VWL 55/8.1 A",
  "hydraulikplan_nr": null,
  "at_abschaltgrenze": "17",
  "heizkurve": "1,1"
}
"""


def extract_from_pdf_bytes(pdf_bytes_list: list, api_key: str) -> dict:
    """
    Sendet PDFs direkt an Gemini (native PDF-Unterstützung).
    Gibt ein Dict zurück das direkt in session_state.form geschrieben werden kann.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    # PDFs als inline_data an Gemini übergeben
    parts = [EXTRACTION_PROMPT]
    for pdf_bytes in pdf_bytes_list:
        parts.append({
            "inline_data": {
                "mime_type": "application/pdf",
                "data": base64.b64encode(pdf_bytes).decode("utf-8"),
            }
        })

    response = model.generate_content(parts)
    text = response.text.strip()

    # JSON extrahieren (robust gegen Markdown-Wrapping)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return {}

    raw = json.loads(match.group())

    def val(key):
        v = raw.get(key)
        return str(v).strip() if v is not None and str(v).strip() not in ("", "null", "None") else ""

    result = {}

    if val("projektnummer"):
        result["Anlagennummer"] = val("projektnummer")
    if val("wp_modell"):
        result["AnlagenName"]   = val("wp_modell")
        result["BeschreibungSpitzenlastgeraet"] = val("wp_modell")

    # Adresse – direkt aus den geparsten Feldern
    if val("anlage_strasse"):
        result["AnlageStrasse"]         = val("anlage_strasse")
        result["EigentuemerStrasse"]    = val("anlage_strasse")
    if val("anlage_hausnr"):
        result["AnlageHausnr"]          = val("anlage_hausnr")
        result["EigentuemerHausnr"]     = val("anlage_hausnr")
    if val("anlage_plz"):
        result["AnlagenPLZ"]            = val("anlage_plz")
        result["EigentuemerPLZ"]        = val("anlage_plz")
    if val("anlage_ort"):
        result["AnlagenOrt"]            = val("anlage_ort")
        result["EigentuemerOrt"]        = val("anlage_ort")
    if val("kunde_nachname"):
        result["EigentuemerName"]       = val("kunde_nachname")
    if val("telefon"):
        result["EigentuemerTelefon"]    = val("telefon")
    if val("hydraulikplan_nr"):
        result["2.3"] = val("hydraulikplan_nr")
        result["5.2"] = val("hydraulikplan_nr")
    if val("at_abschaltgrenze"):
        result["11.8"] = val("at_abschaltgrenze")
    if val("heizkurve"):
        result["11.9"] = val("heizkurve")

    return result
