"""
Extrahiert Kundendaten aus Projektdokumenten (PDF) via Gemini.
"""
import json
import re
import io


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Liest den gesamten Text aus einer PDF (alle Seiten)."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


EXTRACTION_PROMPT = """
Du bekommst den Textinhalt eines oder mehrerer Projektdokumente (Auftragsbestätigung, Angebot, Lieferschein o.ä.) für eine Heizungsanlage.

Extrahiere folgende Informationen soweit vorhanden:

- projektnummer: Projektnummer oder Auftragsnummer (z.B. C-1234-567 oder ähnliches Format)
- anlagen_modell: Modellbezeichnung der Wärmepumpe / Hauptgerät
- anlage_strasse: Straße der Anlage / Installationsort
- anlage_hausnr: Hausnummer der Anlage
- anlage_plz: PLZ der Anlage
- anlage_ort: Ort der Anlage
- kunde_anrede: Anrede des Kunden (Herr / Frau)
- kunde_vorname: Vorname des Kunden
- kunde_nachname: Nachname des Kunden
- kunde_strasse: Straße des Kunden (Rechnungsadresse)
- kunde_hausnr: Hausnummer des Kunden
- kunde_plz: PLZ des Kunden
- kunde_ort: Ort des Kunden
- kunde_telefon: Telefonnummer des Kunden
- hydraulikplan_nr: Hydraulikplan-Nummer falls vorhanden
- at_abschaltgrenze: AT-Abschaltgrenze (Zahl, meist 17)
- heizkurve: Heizkurvensteigung (z.B. 1,1)

Antworte NUR als JSON-Objekt. Felder die nicht gefunden werden auf null setzen. Beispiel:
{
  "projektnummer": "C-1234-567",
  "anlagen_modell": "aroTHERM plus VWL 75/8.1 A",
  "anlage_strasse": "Musterstraße",
  "anlage_hausnr": "12",
  "anlage_plz": "80331",
  "anlage_ort": "München",
  "kunde_anrede": "Herr",
  "kunde_vorname": "Max",
  "kunde_nachname": "Mustermann",
  "kunde_strasse": "Musterstraße",
  "kunde_hausnr": "12",
  "kunde_plz": "80331",
  "kunde_ort": "München",
  "kunde_telefon": "089 123456",
  "hydraulikplan_nr": null,
  "at_abschaltgrenze": "17",
  "heizkurve": "1,1"
}
"""


def extract_from_pdf_bytes(pdf_bytes_list: list, api_key: str) -> dict:
    """
    Extrahiert Formulardaten aus einer Liste von PDF-Dateien (als bytes).
    Gibt ein Dict zurück das direkt in session_state.form geschrieben werden kann.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    # Text aus allen PDFs zusammenführen
    combined_text = ""
    for i, pdf_bytes in enumerate(pdf_bytes_list):
        text = extract_text_from_pdf(pdf_bytes)
        combined_text += f"\n\n--- Dokument {i+1} ---\n{text}"

    if not combined_text.strip():
        return {}

    response = model.generate_content([EXTRACTION_PROMPT, combined_text])
    text = response.text.strip()

    # JSON extrahieren
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return {}

    raw = json.loads(match.group())

    # Auf IBN-Formular-Felder mappen
    def val(key):
        v = raw.get(key)
        return str(v) if v is not None else ""

    result = {}

    if val("projektnummer"):
        result["Anlagennummer"] = val("projektnummer")
    if val("anlagen_modell"):
        result["AnlagenName"] = val("anlagen_modell")
    if val("anlage_strasse"):
        result["AnlageStrasse"] = val("anlage_strasse")
    if val("anlage_hausnr"):
        result["AnlageHausnr"] = val("anlage_hausnr")
    if val("anlage_plz"):
        result["AnlagenPLZ"] = val("anlage_plz")
    if val("anlage_ort"):
        result["AnlagenOrt"] = val("anlage_ort")
    if val("kunde_vorname"):
        result["EigentuemerVorname"] = val("kunde_vorname")
    if val("kunde_nachname"):
        result["EigentuemerName"] = val("kunde_nachname")
    if val("kunde_strasse"):
        result["EigentuemerStrasse"] = val("kunde_strasse")
    if val("kunde_hausnr"):
        result["EigentuemerHausnr"] = val("kunde_hausnr")
    if val("kunde_plz"):
        result["EigentuemerPLZ"] = val("kunde_plz")
    if val("kunde_ort"):
        result["EigentuemerOrt"] = val("kunde_ort")
    if val("kunde_telefon"):
        result["EigentuemerTelefon"] = val("kunde_telefon")
    if val("hydraulikplan_nr"):
        result["2.3"] = val("hydraulikplan_nr")
        result["5.2"] = val("hydraulikplan_nr")
    if val("at_abschaltgrenze"):
        result["11.8"] = val("at_abschaltgrenze")
    if val("heizkurve"):
        result["11.9"] = val("heizkurve")

    # Anrede
    anrede_raw = val("kunde_anrede").lower()
    if "frau" in anrede_raw:
        result["EigentuemerAnrede"] = "/2"
    elif "herr" in anrede_raw:
        result["EigentuemerAnrede"] = "/1"

    return result
