import os
import sys

PARTNER_FIRMA = "Vilor GmbH"
PARTNER_KDNR  = "458625"
GEMINI_MODEL  = "gemini-2.5-flash-preview-04-17"

def get_asset_path(relative: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)

BLANKO_PDF = get_asset_path(os.path.join("assets", "Vaillant_IBN_blanko_offline.pdf"))

# Geräte-Zuordnungs-Optionen
DEVICE_ROLES = [
    "– ignorieren –",
    "Wärmepumpe (Spitzenlastgerät)",
    "Pufferspeicher",
    "Trinkwasserspeicher",
    "Regler",
    "Kondensatpumpe",
    "Pumpen",
    "Freie Zeile 7",
    "Freie Zeile 8",
]

# Mapping: Rolle → (Beschreibungs-Feld-ID, Seriennummer-Feld-ID)
ROLE_TO_FIELD = {
    "Wärmepumpe (Spitzenlastgerät)": ("BeschreibungSpitzenlastgeraet", "SerialnummerSpitzenlastgeraet"),
    "Pufferspeicher":                ("BeschreibungPufferspeicher",     "SerialnummerPufferspeicher"),
    "Trinkwasserspeicher":           ("BeschreibungTrinkwasserspeicher","SerialnummerTrinkwasserspeicher"),
    "Regler":                        ("BeschreibungKondensatpumpe",     "SerialnummerKondensatpumpe"),
    "Kondensatpumpe":                ("BeschreibungPumpen",             "SerialnummerPumpen"),
    "Pumpen":                        ("GeraeteBeschreibung06",           "Serialnummer06"),
    "Freie Zeile 7":                 ("GeraeteBeschreibung07",           "Serialnummer07"),
    "Freie Zeile 8":                 ("GeraeteBeschreibung08",           "Serialnummer08"),
}
