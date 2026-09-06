from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import jogadores, liga, valores

app = FastAPI(
    title="Plataforma da Liga MFL",
    description="Backend que serve dados da liga (Sleeper) e da base de jogadores da NFL.",
    version="0.1.0",
)

# Libera o frontend (rodando em outra porta/domínio) a chamar essa API.
# Em produção, troque "*" pela URL real do frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(liga.router)
app.include_router(jogadores.router)
app.include_router(valores.router)


@app.get("/")
def raiz():
    return {"status": "ok", "docs": "/docs"}
