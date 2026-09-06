"""
Configurações centrais da plataforma da liga.

Se um dia vocês jogarem mais de uma temporada com league_id diferente,
troque só o valor abaixo (ou, melhor ainda, leia de uma variável de
ambiente LEAGUE_ID).
"""

import os

LEAGUE_ID = os.getenv("LEAGUE_ID", "1309632074868600832")
SLEEPER_BASE_URL = "https://api.sleeper.app/v1"

# Cache local do arquivo de jogadores (~5MB). O Sleeper recomenda não
# baixar esse endpoint mais de 1x por dia.
PLAYERS_CACHE_PATH = os.getenv("PLAYERS_CACHE_PATH", "players_cache.json")
PLAYERS_CACHE_MAX_AGE_SECONDS = 24 * 60 * 60

# Cache em memória para dados que mudam mais rápido (standings, rosters).
# Em produção isso pode virar Redis; por enquanto, um dicionário simples
# com timestamp já resolve.
LIGA_CACHE_MAX_AGE_SECONDS = 60 * 5  # 5 minutos
