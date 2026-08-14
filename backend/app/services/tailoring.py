"""
Generacion de carta de presentacion y resumen de CV ajustado.

MVP: generacion basada en template (sin costo, sin API key). Si mas adelante
quieres redaccion con IA (mejor calidad), agrega tu ANTHROPIC_API_KEY al
.env y reemplaza `generate_cover_letter` por una llamada a la API de
Claude usando el mismo texto de cv/job como prompt.
"""
from app import models


def generate_cover_letter(user_name: str, cv: models.CV, job: models.Job) -> str:
    top_skills = ", ".join(cv.skills[:5]) if cv.skills else "mis habilidades tecnicas"
    return (
        f"Estimado equipo de {job.company or 'la empresa'},\n\n"
        f"Mi nombre es {user_name} y me interesa aplicar a la posicion de {job.title}. "
        f"Cuento con experiencia relevante en {top_skills}, que considero se alinea "
        f"directamente con lo que buscan para este puesto.\n\n"
        f"{cv.summary or ''}\n\n"
        f"Quedo atento/a para conversar mas sobre como puedo aportar al equipo.\n\n"
        f"Saludos,\n{user_name}"
    )


def generate_tailored_cv_summary(cv: models.CV, job: models.Job) -> str:
    """Genera un resumen del CV enfatizando lo relevante para esta vacante especifica.
    (No reescribe el CV completo; se usa como bloque de resumen/objetivo a insertar)."""
    job_words = set(job.description.lower().split())
    matched_skills = [s for s in (cv.skills or []) if s.lower() in job_words]
    other_skills = [s for s in (cv.skills or []) if s not in matched_skills]
    ordered_skills = matched_skills + other_skills

    return (
        f"Perfil orientado a: {job.title}\n"
        f"Habilidades destacadas para esta vacante: {', '.join(ordered_skills[:8])}\n\n"
        f"{cv.summary or cv.raw_text[:400]}"
    )
