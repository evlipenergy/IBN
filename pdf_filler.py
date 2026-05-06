import io
from pypdf import PdfReader, PdfWriter


def fill_ibn_bytes_from_bytes(input_bytes: bytes, data: dict) -> bytes:
    """Füllt das IBN-Formular aus bytes (für Streamlit Cloud) und gibt PDF-bytes zurück."""
    reader = PdfReader(io.BytesIO(input_bytes))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, data)

    anrede = data.get("EigentuemerAnrede", "/1")
    writer.update_page_form_field_values(writer.pages[0], {"EigentuemerAnrede": anrede})

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


def fill_ibn_bytes(input_path: str, data: dict) -> bytes:
    """Füllt das IBN-Formular und gibt die PDF als Bytes zurück (für Streamlit Download)."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, data)

    # Radio-Button Anrede separat auf Seite 1
    anrede = data.get("EigentuemerAnrede", "/1")
    writer.update_page_form_field_values(writer.pages[0], {"EigentuemerAnrede": anrede})

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()
