"""
Cliente para o endpoint público de notícias da ESPN. Não é uma API
oficialmente documentada, mas é a mesma usada pelo site/app da ESPN,
estável e usada por vários projetos de fantasy football.
"""

import time
from typing import Any

import requests

ESPN_NEWS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news"

CACHE_MAX_AGE_SECONDS = 15 * 60  # 15 min — notícias mudam rápido, mas não precisa bater toda hora
_cache: dict[str, Any] = {"timestamp": 0, "dados": None}


def _melhor_imagem(imagens: list[dict]) -> str | None:
    """Prioriza uma imagem 16:9 de tamanho razoável; se não achar, usa a primeira disponível."""
    for img in imagens:
        if img.get("ratio") == "16x9" and img.get("width", 0) >= 600:
            return img.get("url")
    for img in imagens:
        if img.get("url"):
            return img.get("url")
    return None


def _simplificar(artigo: dict) -> dict:
    times = []
    jogadores = []
    for cat in artigo.get("categories", []):
        if cat.get("type") == "team" and cat.get("team", {}).get("abbreviation"):
            times.append(cat["team"]["abbreviation"])
        elif cat.get("type") == "athlete" and cat.get("athlete", {}).get("description"):
            jogadores.append(cat["athlete"]["description"])

    return {
        "id": artigo.get("id"),
        "titulo": artigo.get("headline"),
        "resumo": artigo.get("description"),
        "publicado_em": artigo.get("published"),
        "imagem": _melhor_imagem(artigo.get("images", [])),
        "link": artigo.get("links", {}).get("web", {}).get("href"),
        "times": sorted(set(times)),
        "jogadores": sorted(set(jogadores)),
    }


def get_nfl_news(limit: int = 50) -> list[dict]:
    """
    Últimas notícias da NFL, já simplificadas. Cacheado por 15 minutos
    em memória — não precisa ser mais em tempo real que isso pra um
    painel de liga entre amigos.
    """
    agora = time.time()
    if _cache["dados"] is not None and (agora - _cache["timestamp"]) < CACHE_MAX_AGE_SECONDS:
        return _cache["dados"]

    try:
        resp = requests.get(ESPN_NEWS_URL, params={"limit": limit}, timeout=15)
        resp.raise_for_status()
        artigos = resp.json().get("articles", [])
    except Exception:
        return _cache["dados"] or []

    resultado = [_simplificar(a) for a in artigos if a.get("type") != "Media"]

    _cache["dados"] = resultado
    _cache["timestamp"] = agora
    return resultado
