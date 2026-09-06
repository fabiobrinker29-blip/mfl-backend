from fastapi import APIRouter, Query

from app.services.espn_client import get_nfl_news

router = APIRouter(prefix="/noticias", tags=["noticias"])


@router.get("")
def listar_noticias(
    time_nfl: str | None = Query(None, description="Filtra por sigla do time, ex: KC"),
    limite: int = Query(30, le=50),
):
    """Últimas notícias da NFL (fonte: ESPN), com foto, resumo e link pra matéria completa."""
    noticias = get_nfl_news(limit=50)

    if time_nfl:
        sigla = time_nfl.upper()
        noticias = [n for n in noticias if sigla in n["times"]]

    return noticias[:limite]
