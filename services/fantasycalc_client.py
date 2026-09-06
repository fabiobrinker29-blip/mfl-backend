"""
Cliente para a API pública do FantasyCalc — a mesma que alimenta o site
deles (fantasycalc.com). Usamos pra puxar os valores de troca dos
jogadores, calibrados pro formato exato da liga.
"""

import time
from typing import Any

import requests

FANTASYCALC_URL = "https://api.fantasycalc.com/values/current"

# Formato da liga MFL: 10 times, PPR completo, 1 QB titular, redraft
# (não é dynasty — o elenco reseta a cada temporada).
PARAMETROS_LIGA = {
    "isDynasty": "false",
    "numQbs": 1,
    "numTeams": 10,
    "ppr": 1,
}

CACHE_MAX_AGE_SECONDS = 3 * 60 * 60  # 3h — o FantasyCalc atualiza algumas vezes por dia
_cache: dict[str, Any] = {"timestamp": 0, "dados": None}


def _buscar_valores_brutos() -> list[dict]:
    resp = requests.get(FANTASYCALC_URL, params=PARAMETROS_LIGA, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_valores_jogadores() -> list[dict]:
    """
    Retorna a lista de jogadores com valor de troca, já simplificada:
    player_id (= sleeperId, pra casar com o resto do sistema), nome,
    posição, time da NFL e o valor numérico calculado pelo FantasyCalc.

    Jogadores sem sleeperId mapeado são ignorados (não daria pra casar
    com o resto do app de qualquer forma).
    """
    agora = time.time()
    if _cache["dados"] is not None and (agora - _cache["timestamp"]) < CACHE_MAX_AGE_SECONDS:
        return _cache["dados"]

    brutos = _buscar_valores_brutos()
    resultado = []
    for item in brutos:
        jogador = item.get("player", {})
        sleeper_id = jogador.get("sleeperId")
        if not sleeper_id:
            continue
        resultado.append(
            {
                "player_id": sleeper_id,
                "nome": jogador.get("name"),
                "posicao": jogador.get("position"),
                "time_nfl": jogador.get("maybeTeam"),
                "valor": item.get("value"),
                "overall_rank": item.get("overallRank"),
            }
        )

    _cache["dados"] = resultado
    _cache["timestamp"] = agora
    return resultado
