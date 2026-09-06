from fastapi import APIRouter

from app.services.sleeper_client import sleeper

router = APIRouter(prefix="/liga", tags=["liga"])


@router.get("/info")
def info():
    """Nome da liga, temporada, número de times, configurações de pontuação."""
    return sleeper.get_league_info()


@router.get("/participantes")
def participantes():
    """Lista de quem joga na liga."""
    users = sleeper.get_league_users()
    return [
        {
            "user_id": u["user_id"],
            "nome": u["display_name"],
            "avatar": u.get("avatar"),
        }
        for u in users
    ]


@router.get("/standings")
def standings():
    """
    Classificação atual: dono do time, vitórias, derrotas, pontos.
    Antes do draft, vitórias/derrotas/pontos vêm zerados — é o estado
    normal da liga em pré-temporada.
    """
    users_by_id = {u["user_id"]: u["display_name"] for u in sleeper.get_league_users()}
    rosters = sleeper.get_league_rosters()

    resultado = []
    for r in rosters:
        settings = r.get("settings", {})
        resultado.append(
            {
                "roster_id": r["roster_id"],
                "dono": users_by_id.get(r["owner_id"], "??"),
                "vitorias": settings.get("wins", 0),
                "derrotas": settings.get("losses", 0),
                "empates": settings.get("ties", 0),
                "pontos": settings.get("fpts", 0) + settings.get("fpts_decimal", 0) / 100,
            }
        )
    resultado.sort(key=lambda x: (-x["vitorias"], -x["pontos"]))
    return resultado


@router.get("/draft-status")
def draft_status():
    """Diz se o draft já rolou — útil pro frontend decidir o que mostrar."""
    return {"draft_realizado": sleeper.league_has_drafted()}


@router.get("/confrontos")
def confrontos_da_rodada():
    """
    Os confrontos da rodada atual (ou a próxima a ser disputada):
    quem enfrenta quem, e o placar se já tiver rolado.
    """
    users_by_id = {u["user_id"]: u["display_name"] for u in sleeper.get_league_users()}
    rosters = sleeper.get_league_rosters()
    dono_por_roster = {r["roster_id"]: users_by_id.get(r["owner_id"], "??") for r in rosters}

    semana_atual = 1
    for semana in range(1, 19):
        matchups = sleeper.get_matchups(semana)
        if not matchups:
            break
        semana_atual = semana
        semana_zerada = all((m.get("points") or 0) == 0 for m in matchups)
        if semana_zerada:
            break

    matchups = sleeper.get_matchups(semana_atual)
    por_matchup: dict[int, list[dict]] = {}
    for m in matchups:
        matchup_id = m.get("matchup_id")
        if matchup_id is None:
            continue
        por_matchup.setdefault(matchup_id, []).append(m)

    resultado = []
    for confronto in por_matchup.values():
        if len(confronto) != 2:
            continue
        a, b = confronto
        resultado.append(
            {
                "semana": semana_atual,
                "dono_a": dono_por_roster.get(a["roster_id"], "??"),
                "pontos_a": a.get("points") or 0,
                "dono_b": dono_por_roster.get(b["roster_id"], "??"),
                "pontos_b": b.get("points") or 0,
                "jogado": (a.get("points") or 0) > 0 or (b.get("points") or 0) > 0,
            }
        )
    return {"semana": semana_atual, "confrontos": resultado}


@router.get("/historico")
def historico_temporada():
    """
    Confrontos de cada rodada da temporada, já achatados por time:
    cada jogo aparece uma vez para cada lado, com adversário, placar
    e resultado (V/D/E). O frontend filtra por 'dono' pra montar o
    histórico de um time específico.

    Antes da temporada começar (ou nas semanas ainda não jogadas),
    simplesmente não há entradas — não é erro, é o estado normal.
    """
    users_by_id = {u["user_id"]: u["display_name"] for u in sleeper.get_league_users()}
    rosters = sleeper.get_league_rosters()
    dono_por_roster = {r["roster_id"]: users_by_id.get(r["owner_id"], "??") for r in rosters}

    jogos = []
    for semana in range(1, 19):
        matchups = sleeper.get_matchups(semana)
        if not matchups:
            continue

        por_matchup: dict[int, list[dict]] = {}
        for m in matchups:
            matchup_id = m.get("matchup_id")
            if matchup_id is None:
                continue
            por_matchup.setdefault(matchup_id, []).append(m)

        houve_jogo_na_semana = False
        for confronto in por_matchup.values():
            if len(confronto) != 2:
                continue
            a, b = confronto
            if (a.get("points") or 0) == 0 and (b.get("points") or 0) == 0:
                continue  # semana ainda não jogada
            houve_jogo_na_semana = True

            for time, adversario in ((a, b), (b, a)):
                pontos = time.get("points") or 0
                pontos_adv = adversario.get("points") or 0
                if pontos > pontos_adv:
                    resultado = "V"
                elif pontos < pontos_adv:
                    resultado = "D"
                else:
                    resultado = "E"
                jogos.append(
                    {
                        "semana": semana,
                        "roster_id": time["roster_id"],
                        "dono": dono_por_roster.get(time["roster_id"], "??"),
                        "pontos": pontos,
                        "adversario_roster_id": adversario["roster_id"],
                        "adversario_dono": dono_por_roster.get(adversario["roster_id"], "??"),
                        "pontos_adversario": pontos_adv,
                        "resultado": resultado,
                    }
                )

        if not houve_jogo_na_semana:
            # Sleeper às vezes já devolve o "esqueleto" de semanas futuras;
            # se a semana inteira está zerada, para de olhar as próximas.
            break

    return jogos
