"""
IBN-Tool – Vaillant Inbetriebnahmeprotokoll (Streamlit Web-App)
"""
import streamlit as st
from PIL import Image
from datetime import date
import os

import config
import pdf_filler
import gemini_extractor

# ---------------------------------------------------------------------------
# Seiten-Konfiguration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="IBN-Tool – Vaillant",
    page_icon="🔧",
    layout="wide",
)

st.title("🔧 IBN-Tool – Vaillant Inbetriebnahmeprotokoll")

# ---------------------------------------------------------------------------
# Session State initialisieren
# ---------------------------------------------------------------------------
FORM_DEFAULTS = {
    "AnlagenName":              "",
    "Anlagennummer":            "",
    "AnlageStrasse":            "",
    "AnlageHausnr":             "",
    "AnlagenPLZ":               "",
    "AnlagenOrt":               "",
    "PartnerFirma1":            config.PARTNER_FIRMA,
    "PartnerKDNR":              config.PARTNER_KDNR,
    "EigentuemerAnrede":        "/1",
    "EigentuemerVorname":       "",
    "EigentuemerName":          "",
    "EigentuemerStrasse":       "",
    "EigentuemerHausnr":        "",
    "EigentuemerPLZ":           "",
    "EigentuemerOrt":           "",
    "EigentuemerTelefon":       "",
    "Datum":                    date.today().strftime("%d.%m.%Y"),
    # Geräte
    "BeschreibungSpitzenlastgeraet":  "",
    "SerialnummerSpitzenlastgeraet":  "",
    "BeschreibungPufferspeicher":     "",
    "SerialnummerPufferspeicher":     "",
    "BeschreibungTrinkwasserspeicher":"",
    "SerialnummerTrinkwasserspeicher":"",
    "BeschreibungKondensatpumpe":     "",   # = Regler (interne ID!)
    "SerialnummerKondensatpumpe":     "",
    "BeschreibungPumpen":             "",   # = Kondensatpumpe
    "SerialnummerPumpen":             "",
    "GeraeteBeschreibung06":          "",
    "Serialnummer06":                 "",
    "GeraeteLabel07":                 "",
    "GeraeteBeschreibung07":          "",
    "Serialnummer07":                 "",
    "GeraeteLabel08":                 "",
    "GeraeteBeschreibung08":          "",
    "Serialnummer08":                 "",
    # Einstellwerte
    "2.3":   "",
    "5.2":   "",
    "11.8":  "17",
    "11.9":  "1,1",
}

if "form" not in st.session_state:
    st.session_state.form = FORM_DEFAULTS.copy()

if "extracted_devices" not in st.session_state:
    st.session_state.extracted_devices = []

if "role_assignments" not in st.session_state:
    st.session_state.role_assignments = []

if "api_key" not in st.session_state:
    # Automatisch aus Streamlit Secrets laden (Streamlit Cloud)
    # Fallback: leerer String → manuelle Eingabe im UI
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2 = st.tabs(["📷  Fotos & Extraktion", "📋  IBN-Formular"])


# ===========================================================================
# TAB 1 – Fotos & Extraktion
# ===========================================================================
with tab1:

    # API-Key – aus Secrets (Cloud) oder manuelle Eingabe (lokal)
    if st.session_state.api_key:
        st.success("🔑 Gemini API-Key ist hinterlegt.", icon="✅")
    else:
        with st.expander("🔑 Gemini API-Key eingeben", expanded=True):
            st.info("Lokal: API-Key hier eingeben. Auf Streamlit Cloud wird er automatisch aus den Secrets geladen.")
            api_input = st.text_input(
                "API-Key",
                value="",
                type="password",
                placeholder="AIza…",
            )
            if st.button("Speichern", key="save_key"):
                st.session_state.api_key = api_input
                st.rerun()

    st.divider()

    # Foto-Upload
    st.subheader("Typenschild-Fotos")
    uploaded_files = st.file_uploader(
        "Fotos hochladen (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        cols = st.columns(min(len(uploaded_files), 5))
        for i, f in enumerate(uploaded_files):
            with cols[i % 5]:
                st.image(f, caption=f.name, use_container_width=True)

    st.divider()

    # Extraktion
    if st.button("🔍  Seriennummern extrahieren (Gemini)", type="primary",
                 disabled=not uploaded_files):
        if not st.session_state.api_key:
            st.error("Bitte zuerst den Gemini API-Key eingeben.")
        else:
            with st.spinner("Gemini analysiert die Typenschilder…"):
                try:
                    images = [Image.open(f) for f in uploaded_files]
                    devices = gemini_extractor.extract_from_pil_images(
                        images, st.session_state.api_key
                    )
                    st.session_state.extracted_devices = devices
                    st.session_state.role_assignments = [
                        _guess_role(d.get("modell", "")) for d in devices
                    ]
                    st.success(f"✅ {len(devices)} Gerät(e) erkannt.")
                except Exception as e:
                    st.error(f"Fehler: {e}")

    # Ergebnis-Tabelle mit Zuordnung
    if st.session_state.extracted_devices:
        st.subheader("Erkannte Geräte – Zuordnung")

        new_assignments = []
        for i, dev in enumerate(st.session_state.extracted_devices):
            col1, col2, col3, col4, col5 = st.columns([2, 4, 4, 1, 3])
            with col1:
                st.write(dev.get("hersteller") or "?")
            with col2:
                st.write(dev.get("modell") or "–")
            with col3:
                st.write(dev.get("seriennummer") or "–")
            with col4:
                st.write(dev.get("leistung_kw") or "")
            with col5:
                current = st.session_state.role_assignments[i] if i < len(st.session_state.role_assignments) else config.DEVICE_ROLES[0]
                idx = config.DEVICE_ROLES.index(current) if current in config.DEVICE_ROLES else 0
                role = st.selectbox(
                    f"Zuordnung {i+1}",
                    options=config.DEVICE_ROLES,
                    index=idx,
                    key=f"role_{i}",
                    label_visibility="collapsed",
                )
                new_assignments.append(role)

        st.session_state.role_assignments = new_assignments

        st.divider()
        if st.button("✅  Zuordnung ins Formular übernehmen", type="primary"):
            count = 0
            for i, dev in enumerate(st.session_state.extracted_devices):
                role = st.session_state.role_assignments[i]
                if role == "– ignorieren –" or role not in config.ROLE_TO_FIELD:
                    continue
                desc_field, sn_field = config.ROLE_TO_FIELD[role]
                st.session_state.form[desc_field] = dev.get("modell") or ""
                st.session_state.form[sn_field]   = dev.get("seriennummer") or ""
                count += 1
            st.success(f"✅ {count} Gerät(e) ins Formular übertragen → jetzt Tab 'IBN-Formular' öffnen.")


def _guess_role(modell: str) -> str:
    m = modell.lower()
    if any(x in m for x in ["vwl", "arotherm", "wärmepumpe", "heat pump"]):
        return "Wärmepumpe (Spitzenlastgerät)"
    if any(x in m for x in ["vps", "puffer", "cwpps"]):
        return "Pufferspeicher"
    if any(x in m for x in ["vih", "unistore", "trinkwasser", "cww", "lapesa"]):
        return "Trinkwasserspeicher"
    if any(x in m for x in ["vrc", "vr 7", "vr 9", "regler", "controller"]):
        return "Regler"
    if "pumpe" in m:
        return "Kondensatpumpe"
    return "– ignorieren –"


# ===========================================================================
# TAB 2 – IBN-Formular
# ===========================================================================
with tab2:

    f = st.session_state.form   # Shortcut

    def field(label, key, readonly=False, width_pct=100):
        if readonly:
            st.text_input(label, value=f[key], disabled=True, key=f"fi_{key}")
        else:
            val = st.text_input(label, value=f[key], key=f"fi_{key}")
            f[key] = val

    # ---- Anlage ----
    st.subheader("📍 Anlage & Standort")
    c1, c2 = st.columns(2)
    with c1:
        f["AnlagenName"]   = st.text_input("Anlagenname / WP-Modell",    value=f["AnlagenName"],   key="fi_AnlagenName")
        f["AnlageStrasse"] = st.text_input("Straße (Anlage)",             value=f["AnlageStrasse"], key="fi_AnlageStrasse")
        f["AnlagenPLZ"]    = st.text_input("PLZ (Anlage)",                value=f["AnlagenPLZ"],    key="fi_AnlagenPLZ")
    with c2:
        f["Anlagennummer"] = st.text_input("Projektnummer (C-XXXX-…)",    value=f["Anlagennummer"], key="fi_Anlagennummer")
        f["AnlageHausnr"]  = st.text_input("Hausnr. (Anlage)",            value=f["AnlageHausnr"],  key="fi_AnlageHausnr")
        f["AnlagenOrt"]    = st.text_input("Ort (Anlage)",                value=f["AnlagenOrt"],    key="fi_AnlagenOrt")

    st.divider()

    # ---- Partner ----
    st.subheader("🏢 Partner (fest)")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Firma",  value=config.PARTNER_FIRMA, disabled=True)
    with c2:
        st.text_input("KD-NR", value=config.PARTNER_KDNR,  disabled=True)

    st.divider()

    # ---- Eigentümer ----
    st.subheader("👤 Eigentümer")
    anrede_label = st.radio("Anrede", ["Herr", "Frau"], horizontal=True,
                            index=0 if f["EigentuemerAnrede"] == "/1" else 1,
                            key="fi_anrede")
    f["EigentuemerAnrede"] = "/1" if anrede_label == "Herr" else "/2"

    c1, c2 = st.columns(2)
    with c1:
        f["EigentuemerVorname"]  = st.text_input("Vorname",   value=f["EigentuemerVorname"],  key="fi_EigVn")
        f["EigentuemerStrasse"]  = st.text_input("Straße",    value=f["EigentuemerStrasse"],  key="fi_EigStr")
        f["EigentuemerPLZ"]      = st.text_input("PLZ",       value=f["EigentuemerPLZ"],      key="fi_EigPLZ")
        f["EigentuemerTelefon"]  = st.text_input("Telefon",   value=f["EigentuemerTelefon"],  key="fi_EigTel")
    with c2:
        f["EigentuemerName"]     = st.text_input("Nachname",  value=f["EigentuemerName"],     key="fi_EigNn")
        f["EigentuemerHausnr"]   = st.text_input("Hausnr.",   value=f["EigentuemerHausnr"],   key="fi_EigHnr")
        f["EigentuemerOrt"]      = st.text_input("Ort",       value=f["EigentuemerOrt"],      key="fi_EigOrt")
        f["Datum"]               = st.text_input("Datum",     value=f["Datum"],               key="fi_Datum")

    st.divider()

    # ---- Geräte ----
    st.subheader("⚙️ Geräte")

    devices_cfg = [
        ("Wärmepumpe – Modell",          "BeschreibungSpitzenlastgeraet"),
        ("Wärmepumpe – Seriennummer",     "SerialnummerSpitzenlastgeraet"),
        ("Pufferspeicher – Modell",       "BeschreibungPufferspeicher"),
        ("Pufferspeicher – Seriennummer", "SerialnummerPufferspeicher"),
        ("Trinkwasserspeicher – Modell",       "BeschreibungTrinkwasserspeicher"),
        ("Trinkwasserspeicher – Seriennummer", "SerialnummerTrinkwasserspeicher"),
        ("Regler – Modell",               "BeschreibungKondensatpumpe"),
        ("Regler – Seriennummer",         "SerialnummerKondensatpumpe"),
        ("Kondensatpumpe – Modell",       "BeschreibungPumpen"),
        ("Kondensatpumpe – Seriennummer", "SerialnummerPumpen"),
        ("Pumpen – Modell",               "GeraeteBeschreibung06"),
        ("Pumpen – Seriennummer",         "Serialnummer06"),
    ]

    for i in range(0, len(devices_cfg), 2):
        c1, c2 = st.columns(2)
        lbl1, key1 = devices_cfg[i]
        with c1:
            f[key1] = st.text_input(lbl1, value=f[key1], key=f"fi_{key1}")
        if i + 1 < len(devices_cfg):
            lbl2, key2 = devices_cfg[i + 1]
            with c2:
                f[key2] = st.text_input(lbl2, value=f[key2], key=f"fi_{key2}")

    # Freie Zeilen
    st.markdown("**Freie Zeilen**")
    for row_num in [7, 8]:
        key_label = f"GeraeteLabel0{row_num}"
        key_desc  = f"GeraeteBeschreibung0{row_num}"
        key_sn    = f"Serialnummer0{row_num}"
        c1, c2, c3 = st.columns(3)
        with c1:
            f[key_label] = st.text_input(f"Zeile {row_num} – Label", value=f[key_label], key=f"fi_{key_label}")
        with c2:
            f[key_desc]  = st.text_input(f"Zeile {row_num} – Modell", value=f[key_desc],  key=f"fi_{key_desc}")
        with c3:
            f[key_sn]    = st.text_input(f"Zeile {row_num} – Seriennr.", value=f[key_sn], key=f"fi_{key_sn}")

    st.divider()

    # ---- Einstellwerte ----
    st.subheader("🌡️ Einstellwerte")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f["2.3"]  = st.text_input("Hydraulikplan-Nr. (2.3)", value=f["2.3"],  key="fi_23")
    with c2:
        f["5.2"]  = st.text_input("Hydraulikplan-Nr. (5.2)", value=f["5.2"],  key="fi_52")
    with c3:
        f["11.8"] = st.text_input("AT-Abschaltgrenze °C (11.8)", value=f["11.8"], key="fi_118")
    with c4:
        f["11.9"] = st.text_input("Heizkurvensteigung (11.9)",    value=f["11.9"], key="fi_119")

    st.divider()

    # ---- PDF generieren ----
    st.subheader("📄 PDF generieren")

    col_btn, col_reset = st.columns([2, 1])

    with col_btn:
        if not os.path.exists(config.BLANKO_PDF):
            st.error(
                f"Blanko-PDF nicht gefunden: `{config.BLANKO_PDF}`\n\n"
                "Bitte `Vaillant_IBN_blanko_offline.pdf` in den Ordner `assets/` legen."
            )
        else:
            try:
                data = dict(f)
                pdf_bytes = pdf_filler.fill_ibn_bytes(config.BLANKO_PDF, data)
                nachname  = f.get("EigentuemerName", "").strip()
                filename  = f"IBN_{nachname}.pdf" if nachname else "IBN_Protokoll.pdf"

                st.download_button(
                    label="⬇️  PDF herunterladen",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary",
                )
            except Exception as e:
                st.error(f"PDF-Fehler: {e}")

    with col_reset:
        if st.button("🗑️  Formular leeren"):
            st.session_state.form = FORM_DEFAULTS.copy()
            st.rerun()
