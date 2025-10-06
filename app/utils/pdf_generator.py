# app/utils/pdf_generator.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Any

from jinja2 import Environment, FileSystemLoader

# ReportLab (layout avanzato)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


# === Percorsi base ===
APP_DIR = Path(__file__).resolve().parents[1]  # .../app
TEMPLATES_PDF_DIR = APP_DIR / "templates" / "pdf"

# Cartella target: app/blueprints/static/download/receipts
RECEIPTS_DIR = APP_DIR / "blueprints" / "static" / "download" / "receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Logo opzionale (prima esistente vince)
POSSIBLE_LOGOS = [
    APP_DIR / "static" / "img" / "logo.png",
    APP_DIR / "blueprints" / "static" / "brand" / "logo.png",
]
LOGO_PATH: Optional[Path] = next((p for p in POSSIBLE_LOGOS if p.exists()), None)


# ----------------- Helpers -----------------
def _format_eur(value: Any) -> str:
    """Formatta in EUR stile IT (1.234,56)."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    s = f"{amount:,.2f}"         # 1,234.56
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def _format_date_it(dt: Optional[datetime]) -> str:
    dt = dt or datetime.utcnow()
    return dt.strftime("%d/%m/%Y")

def _load_text_from_template(donation, campaign, extra: dict) -> str:
    """Renderizza il testo base (se vuoi un .txt ‘plain’ nel PDF)."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PDF_DIR)))
    template = env.get_template("receipt_template.txt")
    return template.render(
        full_name=donation.full_name or "Anonimo",
        email=donation.email,
        amount=_format_eur(donation.amount),
        method=donation.method,
        date=_format_date_it(getattr(donation, "created_at", None)),
        campaign_title=campaign.title,
        receipt_number=extra.get("receipt_number")
    )


# ----------------- API principale -----------------
def generate_receipt(donation, campaign) -> str:
    """
    Genera un PDF in app/blueprints/static/download/receipts
    e ritorna il solo filename (es. 'donation_12.pdf').
    Layout: Certificazione / Dichiarazione di erogazione liberale.
    """
    # Nome file stabile
    filename = f"donation_{donation.id}.pdf"
    pdf_path = RECEIPTS_DIR / filename

    # Metadati
    receipt_number = f"{donation.id:06d}"
    created_at = getattr(donation, "created_at", None)

    # === Dati Associazione (fallback intelligenti) ===
    assoc = getattr(campaign, "association", None) or getattr(campaign, "owner", None)

    association_name = (
        getattr(assoc, "name", None)
        or getattr(campaign, "organization_name", None)
        or "Associazione beneficiaria"
    )
    association_tax_id = (
        getattr(assoc, "tax_id", None)
        or getattr(assoc, "vat_number", None)
        or getattr(campaign, "tax_id", None)
        or "—"
    )
    association_address = (
        getattr(assoc, "address", None)
        or getattr(campaign, "address", None)
        or "—"
    )

    # Eventuali info extra (opzionali)
    donor_fiscal_code = getattr(donation, "fiscal_code", None)  # se nel modello esiste
    payment_ref = getattr(donation, "payment_reference", None)  # es. id stripe o CRO

    # Stili
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Heading1"], alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="Subtle", parent=styles["Normal"], fontSize=9, textColor=colors.grey, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], alignment=TA_LEFT, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Right", parent=styles["Normal"], alignment=TA_RIGHT))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=16*mm,
        bottomMargin=16*mm,
        title=f"Certificazione donazione {receipt_number}",
        author=association_name,
        subject="Dichiarazione di erogazione liberale",
    )

    story = []

    # Header/logo
    if LOGO_PATH:
        try:
            img = Image(str(LOGO_PATH))
            img._restrictSize(42*mm, 22*mm)
            story.append(img)
            story.append(Spacer(1, 6))
        except Exception:
            pass

    # Titolo documento
    story.append(Paragraph("Certificazione di Erogazione Liberale", styles["TitleCenter"]))
    story.append(Paragraph(f"Ricevuta n. {receipt_number} – {campaign.title}", styles["Subtle"]))
    story.append(Spacer(1, 8))

    # Blocco Ente Beneficiario
    story.append(Paragraph("Ente beneficiario", styles["H2"]))
    ente_table = Table(
        [
            ["Denominazione", association_name],
            ["C.F./P.IVA", association_tax_id],
            ["Indirizzo", association_address],
        ],
        colWidths=[35*mm, None],
        hAlign="LEFT",
    )
    ente_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(ente_table)
    story.append(Spacer(1, 8))

    # Blocco Donatore
    story.append(Paragraph("Dati del donatore", styles["H2"]))
    donor_rows = [
        ["Nome/Cognome o Rag. Sociale", donation.full_name or "Anonimo"],
        ["Email", donation.email or "—"],
    ]
    if donor_fiscal_code:
        donor_rows.append(["Codice Fiscale/Partita IVA", donor_fiscal_code])

    donor_table = Table(donor_rows, colWidths=[55*mm, None], hAlign="LEFT")
    donor_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(donor_table)
    story.append(Spacer(1, 8))

    # Dati della donazione
    story.append(Paragraph("Dettaglio della donazione", styles["H2"]))
    donation_rows = [
        ["Data", _format_date_it(created_at)],
        ["Importo", f"€ {_format_eur(donation.amount)}"],
        ["Metodo di pagamento", donation.method or "—"],
        ["Campagna/Progetto", campaign.title],
        ["Numero ricevuta", receipt_number],
    ]
    if payment_ref:
        donation_rows.append(["Riferimento pagamento", payment_ref])

    donation_table = Table(donation_rows, colWidths=[50*mm, None], hAlign="LEFT")
    donation_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(donation_table)
    story.append(Spacer(1, 8))

    # Dichiarazione
    dichiarazione = (
        "La presente donazione è effettuata a titolo di <b>erogazione liberale</b> "
        "e sarà utilizzata esclusivamente per le <b>finalità istituzionali</b> dell’ente beneficiario. "
        "Il presente documento è rilasciato ai fini delle agevolazioni fiscali previste dalla normativa vigente."
    )
    story.append(Paragraph("Dichiarazione", styles["H2"]))
    story.append(Paragraph(dichiarazione, styles["Normal"]))
    story.append(Spacer(1, 10))

    # Firma & Timbro
    firma_table = Table(
        [
            ["Luogo e data", "Firma e timbro dell’associazione"],
            [association_address if association_address != "—" else "__________________", "_____________________________"],
        ],
        colWidths=[90*mm, None],
        hAlign="LEFT",
    )
    firma_table.setStyle(TableStyle([
        ("LINEABOVE", (0,1), (0,1), 0.3, colors.grey),
        ("LINEABOVE", (1,1), (1,1), 0.3, colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.grey),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(firma_table)
    story.append(Spacer(1, 8))

    # Footer note legali (facoltative)
    note = (
        "Documento generato automaticamente. In caso di pagamento elettronico (es. carta/Stripe), "
        "fa fede la transazione registrata. Conservare il presente documento per la dichiarazione dei redditi."
    )
    story.append(Paragraph(note, styles["Small"]))

    # Costruisci PDF
    doc.build(story)

    return filename

