"""
Construye el texto del CV a partir de las experiencias laborales capturadas
por el usuario, y genera un PDF descargable con ese contenido.
"""
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

from app import models


def build_cv_text(full_name: str, summary: str | None, skills: list[str], experiences: list[models.WorkExperience]) -> str:
    """Compila un texto de CV plano a partir del resumen, habilidades y experiencias,
    ordenadas de la mas reciente a la mas antigua (por fecha de creacion del registro)."""
    parts = [full_name.upper()]

    if summary:
        parts.append("\nRESUMEN PROFESIONAL")
        parts.append(summary)

    if skills:
        parts.append("\nHABILIDADES")
        parts.append(", ".join(skills))

    if experiences:
        parts.append("\nEXPERIENCIA LABORAL")
        for exp in experiences:
            period = f"{exp.start_period} - {exp.end_period or 'Actualidad'}"
            location_str = f" | {exp.location}" if exp.location else ""
            parts.append(f"\n{exp.job_title} — {exp.company}{location_str}")
            parts.append(period)
            parts.append(exp.description)

    return "\n".join(parts)


def generate_cv_pdf(full_name: str, email: str, summary: str | None, skills: list[str], experiences: list[models.WorkExperience]) -> bytes:
    """Genera un PDF con formato simple y profesional a partir de los datos del CV."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("NameStyle", parent=styles["Title"], fontSize=20, spaceAfter=2)
    contact_style = ParagraphStyle("ContactStyle", parent=styles["Normal"], textColor=colors.grey, spaceAfter=14)
    section_style = ParagraphStyle("SectionStyle", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1a3d7c"))
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10.5, leading=15)
    job_title_style = ParagraphStyle("JobTitleStyle", parent=styles["Normal"], fontSize=11, leading=14, spaceBefore=8, fontName="Helvetica-Bold")
    period_style = ParagraphStyle("PeriodStyle", parent=styles["Normal"], fontSize=9.5, textColor=colors.grey, spaceAfter=4)

    story = []
    story.append(Paragraph(full_name, name_style))
    story.append(Paragraph(email, contact_style))

    if summary:
        story.append(Paragraph("RESUMEN PROFESIONAL", section_style))
        story.append(Paragraph(summary, body_style))

    if skills:
        story.append(Paragraph("HABILIDADES", section_style))
        story.append(Paragraph(", ".join(skills), body_style))

    if experiences:
        story.append(Paragraph("EXPERIENCIA LABORAL", section_style))
        for exp in experiences:
            location_str = f" | {exp.location}" if exp.location else ""
            story.append(Paragraph(f"{exp.job_title} — {exp.company}{location_str}", job_title_style))
            story.append(Paragraph(f"{exp.start_period} - {exp.end_period or 'Actualidad'}", period_style))
            story.append(Paragraph(exp.description.replace("\n", "<br/>"), body_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
