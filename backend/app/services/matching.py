"""
Motor de matching CV <-> vacante.

Usa TF-IDF + similitud de coseno (scikit-learn), que no requiere API keys ni
costo por uso -> apto para plan gratuito. Si mas adelante se quiere mayor
calidad semantica, se puede sustituir `vectorize` por embeddings de OpenAI/
Anthropic/Voyage sin tocar el resto del pipeline (misma firma de funcion).
"""
from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app import models


@dataclass
class MatchResult:
    score: float
    explanation: str


def _build_cv_document(cv: models.CV, prefs: models.Preference | None) -> str:
    parts = [cv.raw_text or "", cv.summary or ""]
    if cv.skills:
        parts.append(" ".join(cv.skills))
    if prefs and prefs.desired_roles:
        parts.append(" ".join(prefs.desired_roles))
    return "\n".join(parts)


def _build_job_document(job: models.Job) -> str:
    return f"{job.title}\n{job.company or ''}\n{job.description}"


def passes_hard_filters(job: models.Job, prefs: models.Preference | None) -> bool:
    """Filtros duros antes de calcular similitud: ubicacion, salario, exclusiones."""
    if not prefs:
        return True

    if prefs.remote_only and not job.remote:
        return False

    if prefs.min_salary and job.salary_max and job.salary_max < prefs.min_salary:
        return False

    text_lower = (job.title + " " + job.description).lower()
    for bad_word in prefs.keywords_exclude or []:
        if bad_word.lower() in text_lower:
            return False

    if prefs.locations:
        loc = (job.location or "").lower()
        if not job.remote and not any(l.lower() in loc for l in prefs.locations):
            return False

    return True


def score_job_against_cv(cv: models.CV, prefs: models.Preference | None, job: models.Job) -> MatchResult:
    cv_doc = _build_cv_document(cv, prefs)
    job_doc = _build_job_document(job)

    vectorizer = TfidfVectorizer(stop_words=None, max_features=2000)
    try:
        tfidf = vectorizer.fit_transform([cv_doc, job_doc])
        sim = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except ValueError:
        # texto vacio o sin vocabulario en comun
        sim = 0.0

    # explicacion simple basada en palabras clave compartidas
    cv_words = set(cv_doc.lower().split())
    job_words = set(job_doc.lower().split())
    shared = list(cv_words.intersection(job_words))[:8]
    explanation = (
        f"Coincidencia por similitud de contenido: {sim:.0%}. "
        f"Terminos en comun: {', '.join(shared) if shared else 'pocos terminos exactos, revisa manualmente'}."
    )

    return MatchResult(score=round(sim, 4), explanation=explanation)


def rank_jobs(cv: models.CV, prefs: models.Preference | None, jobs: list[models.Job], min_score: float = 0.05):
    """Filtra por reglas duras, calcula score y regresa ordenado desc por score."""
    results = []
    for job in jobs:
        if not passes_hard_filters(job, prefs):
            continue
        result = score_job_against_cv(cv, prefs, job)
        if result.score >= min_score:
            results.append((job, result))
    results.sort(key=lambda pair: pair[1].score, reverse=True)
    return results
