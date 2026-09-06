from fastapi import APIRouter

from app.services.fantasycalc_client import get_valores_jogadores

router = APIRouter(prefix="/valores", tags=["valores"])


@router.get("")
def listar_valores():
    """
    Valor de troca de cada jogador, vindo do FantasyCalc e já calibrado
    pro formato da liga (10 times, PPR, 1 QB, redraft). Base da
    calculadora de trade do frontend.
    """
    return get_valores_jogadores()
