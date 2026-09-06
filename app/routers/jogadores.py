from fastapi import APIRouter, Query

from app.services.sleeper_client import sleeper

router = APIRouter(prefix="/jogadores", tags=["jogadores"])

# Sleeper não manda a conferência (AFC/NFC) pronta — mapeamos aqui mesmo.
AFC = {
    "BUF", "MIA", "NE", "NYJ",
    "BAL", "CIN", "CLE", "PIT",
    "HOU", "IND", "JAX", "TEN",
    "DEN", "KC", "LV", "LAC",
}
NFC = {
    "DAL", "NYG", "PHI", "WAS",
    "CHI", "DET", "GB", "MIN",
    "ATL", "CAR", "NO", "TB",
    "ARI", "LAR", "SF", "SEA",
}

# Estatísticas brutas que valem a pena mostrar, quando existirem para o
# jogador — o resto do que o Sleeper manda (snaps, penalidades etc.) a
# gente ignora pra não poluir.
CAMPOS_ESTATISTICA = [
    "pass_yd", "pass_td", "pass_int",
    "rush_att", "rush_yd", "rush_td",
    "rec", "rec_tgt", "rec_yd", "rec_td",
    "fgm", "fga", "xpm",
    "sack", "def_int", "fum_rec", "def_td",
]


def _conferencia(time_nfl: str | None) -> str | None:
    if time_nfl in AFC:
        return "AFC"
    if time_nfl in NFC:
        return "NFC"
    return None


def _temporada_atual() -> str:
    return str(sleeper.get_league_info().get("season", "2026"))


def _resumo(player_id: str, p: dict, stats_por_jogador: dict) -> dict:
    stats = stats_por_jogador.get(player_id, {})
    jogos = stats.get("gp") or 0
    pontos_ppr = stats.get("pts_ppr") or 0

    estatisticas = {campo: stats[campo] for campo in CAMPOS_ESTATISTICA if stats.get(campo)}

    return {
        "player_id": player_id,
        "nome": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
        "posicao": p.get("position"),
        "time_nfl": p.get("team"),
        "conferencia": _conferencia(p.get("team")),
        "status_lesao": p.get("injury_status"),  # None, Questionable, Doubtful, Out, IR...
        "detalhe_lesao": p.get("injury_body_part"),
        "status_ativo": p.get("status"),  # Active, Inactive, etc.
        "foto": f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg",
        "pontos_ppr": round(pontos_ppr, 1),
        "jogos": jogos,
        "media_ppr": round(pontos_ppr / jogos, 1) if jogos else 0,
        "estatisticas": estatisticas,
    }


@router.get("/{player_id}")
def detalhe_jogador(player_id: str):
    """Detalhe de um jogador específico pelo ID do Sleeper, com estatísticas da temporada."""
    players = sleeper.get_all_players()
    p = players.get(player_id)
    if not p:
        return {"erro": "jogador não encontrado"}
    stats = sleeper.get_season_stats(_temporada_atual())
    return _resumo(player_id, p, stats)


@router.get("")
def listar_jogadores(
    time_nfl: str | None = Query(None, description="Filtro por sigla do time, ex: KC"),
    conferencia: str | None = Query(None, description="AFC ou NFC"),
    posicao: str | None = Query(None, description="QB, RB, WR, TE, K, DEF"),
    apenas_lesionados: bool = Query(False, description="Só jogadores com injury_status preenchido"),
    ordenar_por: str = Query("pontos_ppr", description="pontos_ppr, media_ppr ou nome"),
    limite: int = Query(50, le=500),
):
    """
    Painel de jogadores com filtros e estatísticas de pontuação da
    temporada — por padrão, já vem ordenado por quem mais pontuou.
    """
    players = sleeper.get_all_players()
    stats = sleeper.get_season_stats(_temporada_atual())

    resultado = []
    for player_id, p in players.items():
        if not p.get("team"):
            continue  # ignora jogadores sem time (agentes livres/aposentados)
        if time_nfl and p.get("team") != time_nfl.upper():
            continue
        if conferencia and _conferencia(p.get("team")) != conferencia.upper():
            continue
        if posicao and p.get("position") != posicao.upper():
            continue
        if apenas_lesionados and not p.get("injury_status"):
            continue

        resultado.append(_resumo(player_id, p, stats))

    if ordenar_por == "nome":
        resultado.sort(key=lambda j: j["nome"])
    elif ordenar_por == "media_ppr":
        resultado.sort(key=lambda j: j["media_ppr"], reverse=True)
    else:
        resultado.sort(key=lambda j: j["pontos_ppr"], reverse=True)

    return resultado[:limite]
