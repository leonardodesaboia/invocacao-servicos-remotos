# Trabalho 6 — Comparação de Tecnologias de Invocação de Serviços Remotos

Serviço de **streaming de músicas** implementado em **4 tecnologias** de invocação
remota (**SOAP, REST, GraphQL, gRPC**) e **2 linguagens** (**Python** e **Node.js**),
totalizando **8 versões** do mesmo serviço, mais um **arnês de testes de carga**
que compara o desempenho das 8 versões e gera **gráficos**.

> Disciplina: Computação Distribuída — Prof. Nabor C. Mendonça.

---

## 1. O serviço

Gerencia 3 recursos relacionados conforme o diagrama do enunciado:

| Recurso  | Campos                                   | Relações |
|----------|------------------------------------------|----------|
| Usuário  | `id`, `nome`, `idade`                     | possui N playlists |
| Música   | `id`, `nome`, `artista`, `ano`, `album`  | aparece em N playlists |
| Playlist | `id`, `nome`, `usuarioId`, `musicaIds[]` | pertence a 1 usuário, contém N músicas |

Todas as 8 versões oferecem **CRUD completo** dos 3 recursos e as **5 consultas**
do enunciado:

1. Listar todos os usuários
2. Listar todas as músicas
3. Listar as playlists de um usuário
4. Listar as músicas de uma playlist
5. Listar as playlists que contêm uma música

**Persistência em memória** (sem banco de dados): todas as versões carregam, na
inicialização, o mesmo `data/seed.json` (gerado por `data/generate_seed.py`) com
**300 usuários, 500 músicas e 200 playlists**. A lógica de negócio é idêntica
entre as versões (`python/common/store.py` e `node/common/store.js`); o que muda
de uma para outra é **apenas a camada de invocação remota**.

---

## 2. Estrutura

```
data/        seed compartilhado (generate_seed.py -> seed.json)
proto/       streaming.proto (contrato gRPC usado por Python e Node)
python/      common/ + rest/ graphql/ grpc/ soap/   (4 serviços Python)
node/        common/ + rest/ graphql/ grpc/ soap/   (4 serviços Node.js)
loadtest/    loadtest.py (gerador de carga) + plot.py (gráficos) + results/
```

### Portas

| Tecnologia | Python | Node.js |
|------------|--------|---------|
| REST       | 8001   | 8101    |
| GraphQL    | 8002   | 8102    |
| gRPC       | 8003   | 8103    |
| SOAP       | 8004   | 8104    |

---

## 3. Pré-requisitos e instalação

Python 3.12 ou 3.13 e Node.js 18+.

```bash
# (na raiz do projeto)
python -m venv .venv
.venv/Scripts/python -m pip install -r python/requirements.txt   # Windows
# (Linux/Mac:  .venv/bin/pip install -r python/requirements.txt)

cd node && npm install && cd ..
# Se o PowerShell bloquear npm.ps1 no Windows, use: npm.cmd install

python data/generate_seed.py    # gera data/seed.json (já versionado)
```

> **Nota (SOAP em Python):** o `spyne` 2.14 não importa direto no Python 3.12/3.13.
> O módulo `python/common/spyne_py312_fix.py` corrige isso em tempo de execução
> (é importado automaticamente pelo `python/soap/server.py`). Nada a fazer.

---

## 4. Como rodar cada serviço

Python (use o Python do venv):

```bash
PORT=8001 .venv/Scripts/python python/rest/server.py
PORT=8002 .venv/Scripts/python python/graphql/server.py
PORT=8003 .venv/Scripts/python python/grpc/server.py
PORT=8004 .venv/Scripts/python python/soap/server.py
```

Node.js:

```bash
cd node
PORT=8101 node rest/server.js
PORT=8102 node graphql/server.js
PORT=8103 node grpc/server.js
PORT=8104 node soap/server.js
```

### Exemplos rápidos (CRUD operacional)

```bash
# REST
curl http://127.0.0.1:8001/musics
curl http://127.0.0.1:8001/playlists/1/musics
curl -X POST http://127.0.0.1:8001/users -H "Content-Type: application/json" \
     -d '{"nome":"Maria","idade":25}'

# GraphQL
curl -X POST http://127.0.0.1:8002/graphql -H "Content-Type: application/json" \
     -d '{"query":"{ playlist(id:1){ nome usuario{nome} musicas{nome artista} } }"}'

# SOAP — WSDL
curl http://127.0.0.1:8004/?wsdl
```

gRPC: use o stub gerado (`python/grpc/streaming_pb2*.py`) ou `grpcurl`.

---

## 5. Testes de carga e gráficos

O arnês sobe **cada versão isoladamente** (um servidor por vez, para uma medição
justa), aplica a carga e encerra o servidor. Mede **duas operações**
(payload grande × pequeno) sob **vários níveis de concorrência**.

```bash
# benchmark completo (cargas de 10, 50, 100 e 200 usuários simultâneos)
.venv/Scripts/python loadtest/loadtest.py --duration 5 --levels 10 50 100 200

# gera os gráficos PNG a partir do CSV
.venv/Scripts/python loadtest/plot.py
```

Saídas em `loadtest/results/`:

- `results.csv` — vazão (req/s), latência média/p50/p95, nº de requisições e erros
- `throughput_<op>.png`, `latency_<op>.png`, `throughput_vs_carga_<op>.png`

Operações medidas:

- **listMusics** — retorna as 500 músicas (payload grande: estressa
  serialização e transferência).
- **musicsByPlaylist** — retorna ~22 músicas de uma playlist (payload pequeno:
  estressa o overhead por requisição).

---

## 6. Resultados (resumo)

Veja `loadtest/results/` para os números e gráficos completos. Exemplo de vazão
medida com **100 usuários simultâneos** (máquina de teste; valores variam por
hardware):

| Operação           | 1º lugar         | 2º            | … mais lentos                |
|--------------------|------------------|---------------|------------------------------|
| `listMusics` (500) | gRPC/Node ~2350  | REST/Node ~1090 | SOAP/Python ~35, GraphQL/Python ~56 |
| `musicsByPlaylist` | gRPC/Node ~8870  | gRPC/Python ~3730 | GraphQL/Python ~39           |

Leitura geral:

- **gRPC** lidera com folga em vazão e menor latência (HTTP/2 + Protobuf binário).
- **REST** vem logo atrás, com ótimo custo/benefício.
- **GraphQL** tem overhead de parse/execução do schema, mas brilha quando o
  cliente precisa de dados relacionados em uma só requisição.
- **SOAP** é o mais lento (XML verboso + envelope), especialmente em Python
  (spyne com validação lxml).
- Entre linguagens, **Node.js** supera o **Python** em I/O concorrente.

> **Ressalva metodológica:** os serviços HTTP em Python rodam no servidor WSGI de
> desenvolvimento (`wsgiref`, simples), que satura sob alta concorrência — por
> isso GraphQL/Python e REST/Python acusam muitos erros em 100–200 usuários. Em
> produção usaria-se `gunicorn`/`waitress`. Isso não muda a ordem geral (gRPC >
> REST > GraphQL > SOAP), mas explica os números extremos do Python sob carga
> alta. A coluna `errors` do `results.csv` registra isso de forma transparente.

A análise crítica detalhada (origem, características, vantagens/desvantagens de
cada tecnologia, cruzada com estes números) vai na apresentação de slides.
