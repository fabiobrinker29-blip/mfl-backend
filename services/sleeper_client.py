"""
Camada única de acesso à API do Sleeper.

Toda chamada HTTP pra fora do sistema passa por aqui — assim, se amanhã
o Sleeper mudar algo, ou vocês quiserem trocar por outra fonte, só mexe
neste arquivo.
"""

import json
import os
import time
from typing import Any

import requests

from app.config import (
    LEAGUE_ID,
    PLAYERS_CACHE_MAX_AGE_SECONDS,
    PLAYERS_CACHE_PATH,
    SLEEPER_BASE_URL,
)


class SleeperClient:
    def __init__(self, league_id: str = LEAGUE_ID):
        self.league_id = league_id
        self._memory_cache: dict[str, tuple[float, Any]] = {}

    # -------- infraestrutura interna --------

    def _get(self, path: str) -> Any:
        resp = requests.get(f"{SLEEPER_BASE_URL}{path}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _get_cached(self, path: str, max_age_seconds: int) -> Any:
        """Cache simples em memória, pra não bater na API a cada request."""
        now = time.time()
        cached = self._memory_cache.get(path)
        if cached and (now - cached[0]) < max_age_seconds:
            return cached[1]

        data = self._get(path)
        self._memory_cache[path] = (now, data)
        return data

    # -------- endpoints da liga --------

    def get_league_info(self) -> dict:
        from app.config import LIGA_CACHE_MAX_AGE_SECONDS

        return self._get_cached(f"/league/{self.league_id}", LIGA_CACHE_MAX_AGE_SECONDS)

    def get_league_users(self) -> list[dict]:
        from app.config import LIGA_CACHE_MAX_AGE_SECONDS

        return self._get_cached(
            f"/league/{self.league_id}/users", LIGA_CACHE_MAX_AGE_SECONDS
        )

    def get_league_rosters(self) -> list[dict]:
        from app.config import LIGA_CACHE_MAX_AGE_SECONDS

        return self._get_cached(
            f"/league/{self.league_id}/rosters", LIGA_CACHE_MAX_AGE_SECONDS
        )

    def get_matchups(self, week: int) -> list[dict]:
        from app.config import LIGA_CACHE_MAX_AGE_SECONDS

        return self._get_cached(
            f"/league/{self.league_id}/matchups/{week}", LIGA_CACHE_MAX_AGE_SECONDS
        )

    def get_draft_id(self) -> str | None:
        return self.get_league_info().get("draft_id")

    def get_draft_picks(self) -> list[dict]:
        draft_id = self.get_draft_id()
        if not draft_id:
            return []
        from app.config import LIGA_CACHE_MAX_AGE_SECONDS

        return self._get_cached(
            f"/draft/{draft_id}/picks", LIGA_CACHE_MAX_AGE_SECONDS
        )

    def league_has_drafted(self) -> bool:
        """
        True assim que existir ao menos 1 pick feito no draft.
        Uso principal: o frontend decide se já mostra rosters/trade calc
        ou se mostra uma tela de 'aguardando o draft'.
        """
        return len(self.get_draft_picks()) > 0

    # -------- base de jogadores da NFL (arquivo grande, cache em disco) --------

    def get_all_players(self) -> dict:
        if os.path.exists(PLAYERS_CACHE_PATH):
            age = time.time() - os.path.getmtime(PLAYERS_CACHE_PATH)
            if age < PLAYERS_CACHE_MAX_AGE_SECONDS:
                with open(PLAYERS_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)

        players = self._get("/players/nfl")
        with open(PLAYERS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(players, f)
        return players

    # -------- estatísticas de pontuação (temporada) --------

    def get_season_stats(self, season: str, season_type: str = "regular") -> dict:
        """
        Estatísticas acumuladas da temporada por jogador — pontos em
        PPR/meio-PPR/padrão, jogos disputados e as estatísticas brutas
        (jardas, touchdowns, recepções etc). Vem de um endpoint público
        do próprio Sleeper, independente de qualquer liga.

        Se o endpoint falhar por qualquer motivo (ex: temporada sem
        dados ainda), devolve vazio em vez de derrubar a página —
        estatística é um bônus, não deveria quebrar o resto do painel.
        """
        cache_key = f"/stats/nfl/{season_type}/{season}"
        try:
            # cache de 3h — os números mudam ao longo do domingo de
            # jogos, não precisa bater no endpoint a cada request
            return self._get_cached(cache_key, 3 * 60 * 60)
        except Exception:
            return {}


# Instância única compartilhada por toda a aplicação
sleeper = SleeperClient()
