"""
Generacion de carta de presentacion y CV ajustado por vacante.

Principio clave: NUNCA se inventa experiencia, logros, habilidades ni datos
que el usuario no haya capturado. Todo lo que se genera aqui es una
REORGANIZACION del CV real del usuario (su resumen, sus habilidades, sus
experiencias laborales capturadas) priorizando lo mas relevante para cada
vacante especifica. No se agregan frases de relleno con datos ficticios.
"""
from app import models


def _relevance_score(text: str, job_words: set[str]) -> int:
    """Cuenta cuantas palabras del texto (en minusculas) aparecen tambien en la vacante."""
    words = set(text.lower().split())
    return len(words.intersection(job_words))


def generate_tailored_cv(
    full_name: str,
    cv: models.CV,
    experiences: list[models.WorkExperience],
    job: models.Job,
) -> str:
    """Reconstruye el CV del usuario (con sus datos reales) priorizando las
    habilidades y experiencias mas relevantes para esta vacante. No agrega
    texto que el usuario no haya escrito."""
    job_words = set((job.title + " " + job.description).lower().split())

    parts = [full_name.upper()]

    # Resumen: se usa TAL CUAL lo escribio el usuario, sin modificarlo
    if cv and cv.summary:
        parts.append("\nRESUMEN PROFESIONAL")
        parts.append(cv.summary)

    # Habilidades: mismas habilidades que el usuario declaro, solo reordenadas
    # (las que coinciden con la vacante van primero)
    if cv and cv.skills:
        matched = [s for s in cv.skills if s.lower() in job_words]
        rest = [s for s in cv.skills if s not in matched]
        ordered_skills = matched + rest
        parts.append("\nHABILIDADES")
        parts.append(", ".join(ordered_skills))

    # Experiencia: mismas experiencias que el usuario capturo, solo reordenadas
    # por relevancia para esta vacante (mismo texto, mismo contenido)
    if experiences:
        ranked = sorted(
            experiences,
            key=lambda e: _relevance_score(e.job_title + " " + e.description, job_words),
            reverse=True,
        )
        parts.append("\nEXPERIENCIA LABORAL")
        for exp in ranked:
            period = f"{exp.start_period} - {exp.end_period or 'Actualidad'}"
            location_str = f" | {exp.location}" if exp.location else ""
            parts.append(f"\n{exp.job_title} — {exp.company}{location_str}")
            parts.append(period)
            parts.append(exp.description)
    elif cv and cv.raw_text:
        # si el usuario no capturo experiencias estructuradas, se usa el CV tal cual lo escribio
        parts.append("\n" + cv.raw_text)

    return "\n".join(parts)


def generate_cover_letter(
    user_name: str,
    cv: models.CV,
    experiences: list[models.WorkExperience],
    job: models.Job,
) -> str:
    """Genera una carta de presentacion usando solo datos reales del usuario:
    sus habilidades declaradas y su experiencia mas relevante ya capturada.
    No inventa logros, cifras ni responsabilidades."""
    job_words = set((job.title + " " + job.description).lower().split())

    matched_skills = [s for s in (cv.skills or []) if s.lower() in job_words]
    skills_to_mention = matched_skills[:5] if matched_skills else (cv.skills or [])[:5]
    skills_text = ", ".join(skills_to_mention) if skills_to_mention else "mis habilidades tecnicas"

    experience_line = ""
    if experiences:
        most_relevant = max(
            experiences,
            key=lambda e: _relevance_score(e.job_title + " " + e.description, job_words),
        )
        experience_line = (
            f"En mi puesto como {most_relevant.job_title} en {most_relevant.company}, "
            f"desarrolle experiencia directamente relacionada con este puesto.\n\n"
        )

    summary_line = f"{cv.summary}\n\n" if cv and cv.summary else ""

    return (
        f"Estimado equipo de {job.company or 'la empresa'},\n\n"
        f"Mi nombre es {user_name} y me interesa aplicar a la posicion de {job.title}. "
        f"Cuento con experiencia en {skills_text}.\n\n"
        f"{experience_line}"
        f"{summary_line}"
        f"Quedo atento/a para conversar mas sobre como puedo aportar al equipo.\n\n"
        f"Saludos,\n{user_name}"
    )
