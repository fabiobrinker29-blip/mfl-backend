# Plataforma da Liga MFL — Backend

Backend em FastAPI que serve dados da sua liga no Sleeper (league_id
1309632074868600832) e da base de jogadores da NFL.

## Como rodar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Depois acesse http://localhost:8000/docs — o FastAPI gera uma
documentação interativa automática onde dá pra testar cada endpoint
direto no navegador.

## Endpoints disponíveis

- `GET /liga/info` — nome da liga, temporada, configurações
- `GET /liga/participantes` — lista de quem joga
- `GET /liga/standings` — classificação (vitórias/derrotas/pontos)
- `GET /liga/draft-status` — diz se o draft já aconteceu
- `GET /liga/historico` — confrontos de cada rodada, achatados por time (semana, adversário, placar, resultado)
- `GET /jogadores?time_nfl=KC&posicao=WR` — base de jogadores com filtros, foto e pontuação da temporada (já vem ordenado por quem mais pontuou)
- `GET /jogadores?ordenar_por=media_ppr` — reordena por média de pontos por jogo (ou `nome` pra ordem alfabética)
- `GET /jogadores?apenas_lesionados=true` — só quem está no report de lesão
- `GET /jogadores/{player_id}` — detalhe de um jogador específico, com estatísticas da temporada
- `GET /valores` — valor de troca de cada jogador (fonte: FantasyCalc, calibrado pro formato da liga — 10 times, PPR, 1 QB)

## Cache

- Dados da liga (standings, rosters): cache em memória de 5 minutos
- Base de jogadores da NFL (~5MB): cache em disco (`players_cache.json`)
  de 24h, seguindo a recomendação do próprio Sleeper de não bater
  nesse endpoint com frequência

## Variáveis de ambiente (opcionais)

- `LEAGUE_ID` — troca a liga (padrão: a sua liga MFL)
- `PLAYERS_CACHE_PATH` — onde salvar o cache de jogadores

## Próximos passos

- Calculadora de trades (cruzando rosters + tabela de valores de jogadores)
- Páginas personalizadas dos campeões
- Deploy gratuito em Render/Railway
