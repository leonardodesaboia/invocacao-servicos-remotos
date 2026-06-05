# Comparação de Tecnologias de Invocação de Serviços Remotos

> **Computação Distribuída** | Prof. Nabor C. Mendonça

## Integrantes

| Nome | Matrícula |
|------|-----------|
| Leonardo de Saboia      | 231033          |
| Gustavo Fontgalland      | 2315053          |
| Kaíke Petalas     | 2310331          |
| Caio Barros     | 2315082          |

---

Implementação de um **serviço de streaming de músicas** nas quatro tecnologias de invocação remota mais utilizadas — SOAP, REST, GraphQL e gRPC — em duas linguagens (Python e Node.js), com testes de carga comparativos.

---

## Índice

1. [Tecnologias](#1-tecnologias)
   - [SOAP](#soap)
   - [REST](#rest)
   - [GraphQL](#graphql)
   - [gRPC](#grpc)
2. [Comparação Geral](#2-comparação-geral)
3. [Modelo de Dados](#3-modelo-de-dados)
4. [Implementação](#4-implementação)
5. [Testes de Carga](#5-testes-de-carga)
6. [Análise Crítica](#6-análise-crítica)
7. [Como Executar](#7-como-executar)
8. [Referências](#8-referências)

---

## 1. Tecnologias

### SOAP

**Simple Object Access Protocol** — protocolo de troca de mensagens estruturadas, padronizado pelo W3C em 2003, baseado em XML.

**Origem:** Desenvolvido pela Microsoft em 1998 como alternativa ao CORBA e DCE/RPC. Tornou-se padrão W3C em 2003.

**Características:**
- Protocolo formal com contrato WSDL (Web Services Description Language)
- Mensagens em XML encapsuladas em um "envelope" SOAP
- Transporte via HTTP, SMTP ou outros protocolos
- Suporte nativo a segurança (WS-Security), transações e confiabilidade
- Fortemente tipado pelo contrato WSDL

**Exemplo de requisição:**
```xml
POST / HTTP/1.1
Content-Type: text/xml; charset=utf-8
SOAPAction: listMusics

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:tns="streaming.soap">
  <soapenv:Body>
    <tns:listMusics/>
  </soapenv:Body>
</soapenv:Envelope>
```

**Exemplo de resposta:**
```xml
<soapenv:Envelope>
  <soapenv:Body>
    <tns:listMusicsResponse>
      <tns:listMusicsResult>
        <tns:Music>
          <tns:id>1</tns:id>
          <tns:nome>Bohemian Rhapsody</tns:nome>
          <tns:artista>Queen</tns:artista>
        </tns:Music>
      </tns:listMusicsResult>
    </tns:listMusicsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

| | |
|---|---|
| **Vantagens** | Contrato formal (WSDL), segurança nativa (WS-Security), transações distribuídas, independência de transporte |
| **Desvantagens** | Verbosidade extrema do XML, overhead alto, curva de aprendizado, difícil de depurar, pouco adequado para APIs públicas modernas |

---

### REST

**Representational State Transfer** — estilo arquitetural definido por Roy Fielding em sua dissertação de doutorado (2000), não um protocolo.

**Origem:** Descrito por Roy Fielding (UC Irvine, 2000) como um conjunto de restrições arquiteturais para sistemas hipermídia na web. Tornou-se o estilo dominante de APIs web na década de 2010.

**Características:**
- Recursos identificados por URIs (`/musics/42`, `/users/1/playlists`)
- Operações mapeadas nos verbos HTTP (GET, POST, PUT, DELETE)
- Sem estado entre requisições (stateless)
- Representação dos recursos em JSON (ou XML, HTML, etc.)
- Interface uniforme e descoberta via hypermídia (HATEOAS)

**Exemplo de rotas implementadas:**
```
GET    /musics               → lista todas as músicas
GET    /musics/:id           → retorna uma música
POST   /musics               → cria uma música
PUT    /musics/:id           → atualiza uma música
DELETE /musics/:id           → remove uma música

GET    /users/:id/playlists  → playlists de um usuário
GET    /playlists/:id/musics → músicas de uma playlist
GET    /musics/:id/playlists → playlists que contêm a música
```

**Exemplo de requisição e resposta:**
```http
GET /playlists/1/musics HTTP/1.1
Host: localhost:8001
```
```json
[
  { "id": 1, "nome": "Bohemian Rhapsody", "artista": "Queen", "ano": 1975, "album": "A Night at the Opera" },
  { "id": 7, "nome": "Stairway to Heaven", "artista": "Led Zeppelin", "ano": 1971, "album": "Led Zeppelin IV" }
]
```

| | |
|---|---|
| **Vantagens** | Simples, amplamente adotado, cacheable, usa HTTP nativamente, fácil de depurar com ferramentas comuns |
| **Desvantagens** | Overfetching/underfetching de dados, múltiplos round-trips para consultas relacionais, sem contrato formal nativo |

---

### GraphQL

**Graph Query Language** — linguagem de consulta para APIs, desenvolvida pelo Facebook em 2012 e publicada como open source em 2015.

**Origem:** Criado internamente no Facebook para resolver problemas de overfetching e múltiplas chamadas nos apps móveis. Liberado como open source em 2015 e governado pela GraphQL Foundation desde 2019.

**Características:**
- **Um único endpoint** (`/graphql`) para todas as operações
- O cliente especifica exatamente os campos que quer receber
- Schema fortemente tipado (SDL — Schema Definition Language)
- Queries (leitura) e Mutations (escrita) explicitamente separadas
- Navegação de relações em uma única requisição (sem N+1 de round-trips)
- Introspecção nativa do schema

**Schema SDL implementado:**
```graphql
type Music {
  id: Int!
  nome: String!
  artista: String!
  ano: Int!
  album: String!
  playlists: [Playlist!]!   # relação navegável
}

type Query {
  musics: [Music!]!
  musicsByPlaylist(playlistId: Int!): [Music!]!
  playlistsByMusic(musicId: Int!): [Playlist!]!
}

type Mutation {
  createMusic(nome: String!, artista: String!, ano: Int, album: String): Music!
  updateMusic(id: Int!, nome: String, artista: String, ano: Int, album: String): Music!
  deleteMusic(id: Int!): Boolean!
}
```

**Exemplo de query (cliente escolhe apenas os campos necessários):**
```graphql
{
  musicsByPlaylist(playlistId: 1) {
    id
    nome
    artista
  }
}
```

**Exemplo de mutation:**
```graphql
mutation {
  createMusic(nome: "Comfortably Numb", artista: "Pink Floyd", ano: 1979, album: "The Wall") {
    id
    nome
  }
}
```

| | |
|---|---|
| **Vantagens** | Sem overfetching/underfetching, navegação de relações em uma requisição, schema autodocumentado, ideal para frontends com dados variados |
| **Desvantagens** | Complexidade de implementação no servidor, overhead por requisição maior que REST simples, caching HTTP mais difícil, curva de aprendizado |

---

### gRPC

**gRPC Remote Procedure Call** — framework de RPC de alta performance desenvolvido pelo Google, baseado em Protocol Buffers e HTTP/2.

**Origem:** Criado internamente no Google (onde o antecessor "Stubby" estava em uso há mais de uma década). Liberado como open source em 2015. Usado extensivamente em arquiteturas de microsserviços.

**Características:**
- Contrato definido em **Protocol Buffers** (`.proto`) — binário, compacto e fortemente tipado
- Comunicação sobre **HTTP/2** (multiplexing, compressão de cabeçalhos, streams)
- Geração automática de código cliente/servidor em múltiplas linguagens
- Suporte a streaming unidirecional e bidirecional
- Latência muito baixa devido à serialização binária

**Definição `.proto` implementada:**
```protobuf
syntax = "proto3";

message Music {
  int32 id = 1;
  string nome = 2;
  string artista = 3;
  int32 ano = 4;
  string album = 5;
}

service StreamingService {
  rpc ListMusics(Empty)           returns (Musics);
  rpc GetMusic(IdRequest)         returns (Music);
  rpc CreateMusic(MusicInput)     returns (Music);
  rpc UpdateMusic(MusicUpdate)    returns (Music);
  rpc DeleteMusic(IdRequest)      returns (Empty);
  rpc MusicsByPlaylist(IdRequest) returns (Musics);
  rpc PlaylistsByMusic(IdRequest) returns (Playlists);
}
```

**Exemplo de chamada (Python):**
```python
import grpc
import streaming_pb2 as pb
import streaming_pb2_grpc as pbg

channel = grpc.insecure_channel("localhost:8003")
stub = pbg.StreamingServiceStub(channel)

musics = stub.MusicsByPlaylist(pb.IdRequest(id=1))
for m in musics.musics:
    print(m.nome, "-", m.artista)
```

| | |
|---|---|
| **Vantagens** | Altíssima performance, serialização binária eficiente, streaming nativo, geração de código automática, ideal para microsserviços |
| **Desvantagens** | Não legível por humanos (binário), suporte limitado em browsers, ferramentas de debug menos maduras, curva de aprendizado do Protobuf |

---

## 2. Comparação Geral

```
╔══════════════════╦══════════╦══════════╦══════════╦══════════╗
║ Critério         ║  SOAP    ║  REST    ║ GraphQL  ║  gRPC    ║
╠══════════════════╬══════════╬══════════╬══════════╬══════════╣
║ Protocolo        ║ HTTP/SMTP║   HTTP   ║   HTTP   ║  HTTP/2  ║
║ Formato          ║   XML    ║   JSON   ║   JSON   ║  Binário ║
║ Contrato formal  ║  WSDL ✓  ║  ✗ (*)  ║  SDL ✓  ║ .proto ✓ ║
║ Fortemente tipado║    ✓     ║    ✗     ║    ✓     ║    ✓     ║
║ Performance      ║  Baixa   ║  Média   ║  Média   ║  Alta    ║
║ Legibilidade     ║  Baixa   ║  Alta    ║  Alta    ║  Baixa   ║
║ Caching HTTP     ║  Difícil ║  ✓ GET  ║  Difícil ║    ✗     ║
║ Streaming        ║    ✗     ║    ✗     ║  Parcial ║    ✓     ║
║ Browser nativo   ║   Sim    ║   Sim    ║   Sim    ║  Não (**) ║
║ Overfetching     ║   Sim    ║   Sim    ║   Não    ║   Não    ║
║ Uso típico       ║Enterprise║  APIs   ║ Frontend ║Microsserv║
╚══════════════════╩══════════╩══════════╩══════════╩══════════╝
  (*) OpenAPI/Swagger é amplamente adotado como contrato informal
 (**) Requer gRPC-Web ou proxy
```

### Fluxo de comunicação

```
  SOAP
  Cliente ──[XML Envelope]──► POST /  ──► Servidor
           ◄──[XML Response]──────────────

  REST
  Cliente ──[GET /musics]────────────► Servidor
           ◄──[JSON Array]─────────────────

  GraphQL
  Cliente ──[POST /graphql {"query":"..."}]──► Servidor
           ◄──[JSON {"data":{...}}]───────────

  gRPC (HTTP/2, binário)
  Cliente ══[stream multiplexado]════► Servidor
           ◄══[Protobuf binário]═══════
```

---

## 3. Modelo de Dados

O serviço gerencia três recursos relacionados entre si:

```
┌─────────────────────┐          ┌─────────────────────┐
│   <<coleção>>       │          │   <<coleção>>        │
│      Usuários       │          │      Músicas         │
└─────────────────────┘          └─────────────────────┘
           │ 0..*                           │ 0..*
           ▼                               ▼
┌─────────────────────┐          ┌─────────────────────┐
│      Usuário        │          │       Música         │
│─────────────────────│          │─────────────────────│
│  id    : Int        │          │  id     : Int        │
│  nome  : String     │          │  nome   : String     │
│  idade : Int        │          │  artista: String     │
└─────────────────────┘          │  ano    : Int        │
           │ 1..1                │  album  : String     │
           ▼                     └─────────────────────┘
  ┌─────────────────────┐                 ▲ 1..*
  │   <<coleção>>       │                 │
  │      Playlists      │                 │ 0..*
  └─────────────────────┘        ┌────────────────────┐
           │ 0..*                │      Playlist       │
           ▼                     │────────────────────│
                                 │  id       : Int     │
                                 │  nome     : String  │
                                 │  usuarioId: Int     │
                                 └────────────────────┘
```

**Operações suportadas por todas as implementações:**

| # | Consulta | REST | GraphQL | gRPC |
|---|---|---|---|---|
| 1 | Todos os usuários | `GET /users` | `{ users { id nome } }` | `ListUsers(Empty)` |
| 2 | Todas as músicas | `GET /musics` | `{ musics { id nome } }` | `ListMusics(Empty)` |
| 3 | Playlists de um usuário | `GET /users/1/playlists` | `{ playlistsByUser(userId:1) { nome } }` | `PlaylistsByUser({id:1})` |
| 4 | Músicas de uma playlist | `GET /playlists/1/musics` | `{ musicsByPlaylist(playlistId:1) { nome } }` | `MusicsByPlaylist({id:1})` |
| 5 | Playlists com certa música | `GET /musics/1/playlists` | `{ playlistsByMusic(musicId:1) { nome } }` | `PlaylistsByMusic({id:1})` |

---

## 4. Implementação

### Estrutura do projeto

```
.
├── proto/
│   └── streaming.proto          # Contrato gRPC (compartilhado entre Python e Node)
├── python/
│   ├── common/
│   │   └── store.py             # Store em memória (lógica de negócio)
│   ├── rest/     server.py      # Flask        → porta 8001
│   ├── graphql/  server.py      # Ariadne       → porta 8002
│   ├── grpc/     server.py      # grpcio        → porta 8003
│   └── soap/     server.py      # spyne         → porta 8004
├── node/
│   ├── common/
│   │   └── store.js             # Store em memória (lógica de negócio)
│   ├── rest/     server.js      # Express       → porta 8101
│   ├── graphql/  server.js      # graphql-http  → porta 8102
│   ├── grpc/     server.js      # @grpc/grpc-js → porta 8103
│   └── soap/     server.js      # soap          → porta 8104
├── data/
│   ├── seed.json                # 300 usuários, 500 músicas, 200 playlists
│   └── generate_seed.py
└── loadtest/
    ├── loadtest.py              # Motor de testes de carga
    ├── plot.py                  # Gerador de gráficos (matplotlib)
    └── results/
        └── results.csv
```

### Bibliotecas utilizadas

| Tecnologia | Python | Node.js |
|---|---|---|
| REST    | Flask | Express |
| GraphQL | Ariadne | graphql-http |
| gRPC    | grpcio + grpcio-tools | @grpc/grpc-js + @grpc/proto-loader |
| SOAP    | spyne + lxml | soap |

---

## 5. Testes de Carga

### Metodologia

O benchmark (`loadtest/loadtest.py`) sobe cada servidor isoladamente, aplica carga com N threads simultâneas por 5 segundos e mede:

- **Vazão** (req/s): requisições completadas por segundo
- **Latência média** (avg_ms)
- **Latência p95** (ms): 95% das requisições completam abaixo deste valor
- **Erros**: requisições que falharam

**Operações testadas:**
- `listMusics` — retorna as 500 músicas (payload grande, estressa serialização/transferência)
- `musicsByPlaylist` — retorna ~22 músicas de uma playlist (payload pequeno, estressa overhead por requisição)

**Níveis de concorrência:** 10, 50, 100 e 200 threads simultâneas

---

### Resultados: `listMusics` — payload grande (500 músicas)

#### Vazão por tecnologia (todos os níveis de carga)

![Vazão listMusics](loadtest/results/throughput_listMusics.png)

#### Latência p95 por tecnologia (escala logarítmica)

![Latência p95 listMusics](loadtest/results/latency_listMusics.png)

#### Vazão x concorrência (evolução sob aumento de carga)

![Vazão vs carga listMusics](loadtest/results/throughput_vs_carga_listMusics.png)

#### Tabela numérica — `listMusics` (req/s)

```
Tecnologia       │  c=10  │  c=50  │  c=100  │  c=200
─────────────────┼────────┼────────┼─────────┼────────
Node  / gRPC     │ 2008.1 │ 2289.4 │  2351.9 │  2438.5
Node  / REST     │ 1164.6 │ 1095.3 │  1093.0 │  1065.8
Python/ gRPC     │  865.4 │  841.2 │   846.8 │   882.2
Node  / GraphQL  │  374.7 │  393.9 │   388.3 │   398.3
Node  / SOAP     │  375.7 │  383.1 │   390.7 │   386.4
Python/ REST     │  371.1 │  367.8 │   367.1 │   361.9
Python/ GraphQL  │   40.1 │   61.7 │    56.2 │    54.6  ⚠ erros
Python/ SOAP     │   28.1 │   29.2 │    35.0 │    34.0  ⚠ erros
```

---

### Resultados: `musicsByPlaylist` — payload pequeno (~22 músicas)

#### Vazão por tecnologia (todos os níveis de carga)

![Vazão musicsByPlaylist](loadtest/results/throughput_musicsByPlaylist.png)

#### Latência p95 por tecnologia (escala logarítmica)

![Latência p95 musicsByPlaylist](loadtest/results/latency_musicsByPlaylist.png)

#### Vazão x concorrência (evolução sob aumento de carga)

![Vazão vs carga musicsByPlaylist](loadtest/results/throughput_vs_carga_musicsByPlaylist.png)

#### Tabela numérica — `musicsByPlaylist` (req/s)

```
Tecnologia       │   c=10  │   c=50  │  c=100  │  c=200
─────────────────┼─────────┼─────────┼─────────┼─────────
Node  / gRPC     │  7287.8 │  9284.3 │  8864.7 │  8611.4
Python/ gRPC     │  3482.2 │  3581.8 │  3731.5 │  3565.9
Node  / REST     │  1341.7 │  1263.6 │  1300.2 │  1280.0
Node  / SOAP     │  1359.8 │  1305.3 │  1257.8 │  1218.4
Node  / GraphQL  │  1165.0 │  1114.9 │  1020.2 │   998.5
Python/ REST     │   500.8 │   513.4 │   417.9 │     2.0  ⚠ erros
Python/ SOAP     │   330.9 │   314.5 │   318.1 │   297.5
Python/ GraphQL  │    70.6 │    24.2 │    39.4 │    62.3  ⚠ erros
```

---

## 6. Análise Crítica

### Performance

**gRPC** foi a tecnologia mais rápida em todos os cenários, chegando a **8.864 req/s** (Node.js, `musicsByPlaylist`, c=100). Os dois fatores principais são:

1. **Serialização binária (Protocol Buffers):** muito mais compacta e rápida de serializar/deserializar que JSON ou XML
2. **HTTP/2:** multiplexing de requisições em uma única conexão TCP, sem head-of-line blocking

**REST** ficou em segundo lugar, com performance consistente e sem erros em todos os cenários do Node.js. O Node.js (event loop assíncrono) performou 3× melhor que Python (threads síncronas + GIL).

**GraphQL** no Node.js teve performance similar ao REST para payloads pequenos, mas sofreu queda em payloads grandes — o overhead de parsing do schema SDL por requisição se torna relevante. O Python com Ariadne (WSGI síncrono) apresentou erros significativos sob carga alta.

**SOAP** foi o pior para payloads grandes: apenas 35 req/s em Python com latência média de 1.031ms. O XML verboso aumenta drasticamente o custo de serialização e o tamanho da resposta. Em Node.js, porém, performou de forma surpreendentemente competitiva com REST e GraphQL.

### Experiência de desenvolvimento

| Aspecto | SOAP | REST | GraphQL | gRPC |
|---|---|---|---|---|
| Facilidade de implementação | Baixa — geração de WSDL e tipos complexos | Alta — mapeamento direto de recursos | Média — schema SDL + resolvers | Média — .proto + geração de código |
| Depuração | Difícil — XML verboso, ferramentas específicas | Fácil — curl, Postman, browser | Média — GraphiQL facilita | Difícil — payload binário |
| Refatoração | Difícil — mudança no WSDL quebra clientes | Fácil — URLs bem definidas | Fácil — schema é versionável | Média — evolução compatível via field numbers |
| Documentação | Automática via WSDL | Manual (OpenAPI/Swagger) | Automática via introspecção | Automática via .proto |

### Quando usar cada tecnologia?

```
┌──────────────────────────────────────────────────────────────────┐
│  SOAP     → Integrações enterprise, sistemas bancários/legados,  │
│             quando contratos formais e WS-Security são           │
│             obrigatórios (ex.: NF-e, SEFAZ).                    │
├──────────────────────────────────────────────────────────────────┤
│  REST     → APIs públicas, integração web/mobile, recursos bem   │
│             definidos. Escolha padrão pelo tooling maduro e      │
│             familiaridade.                                        │
├──────────────────────────────────────────────────────────────────┤
│  GraphQL  → Frontends com necessidades variadas (mobile vs web), │
│             APIs com muitas relações exploráveis, quando evitar  │
│             overfetching é crítico.                              │
├──────────────────────────────────────────────────────────────────┤
│  gRPC     → Comunicação interna entre microsserviços, sistemas   │
│             onde latência e throughput são críticos, streaming   │
│             de dados em tempo real.                              │
└──────────────────────────────────────────────────────────────────┘
```

> **Nota metodológica:** os servidores HTTP em Python rodam no WSGI de desenvolvimento (`wsgiref`), que satura sob alta concorrência. Em produção usaria-se `gunicorn`/`waitress`. Isso explica os erros do Python sob c=100–200, mas não muda a ordem geral (gRPC > REST > GraphQL > SOAP).

---

## 7. Como Executar

### Pré-requisitos

- Python 3.12+ com virtualenv em `.venv/`
- Node.js 18+

### Instalar dependências

```bash
# Python
.venv/Scripts/python -m pip install flask ariadne grpcio grpcio-tools spyne lxml requests

# Node.js
cd node && npm install
```

### Iniciar um servidor

```bash
# Python
.venv/Scripts/python python/rest/server.py      # REST    → :8001
.venv/Scripts/python python/graphql/server.py   # GraphQL → :8002
.venv/Scripts/python python/grpc/server.py      # gRPC    → :8003
.venv/Scripts/python python/soap/server.py      # SOAP    → :8004

# Node.js
cd node
node rest/server.js      # REST    → :8101
node graphql/server.js   # GraphQL → :8102
node grpc/server.js      # gRPC    → :8103
node soap/server.js      # SOAP    → :8104
```

### Testar manualmente

```bash
# REST — listar músicas
curl http://localhost:8001/musics

# REST — músicas de uma playlist
curl http://localhost:8001/playlists/1/musics

# GraphQL — query
curl -X POST http://localhost:8002/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ musicsByPlaylist(playlistId: 1) { id nome artista } }"}'

# SOAP — WSDL
curl "http://localhost:8004/?wsdl"
```

### Executar testes de carga

```bash
# Benchmark padrão (10, 50, 100 threads, 5s cada)
.venv/Scripts/python loadtest/loadtest.py

# Personalizado
.venv/Scripts/python loadtest/loadtest.py --duration 5 --levels 10 50 100 200

# Gerar gráficos PNG a partir do CSV
.venv/Scripts/python loadtest/plot.py
```

Resultados salvos em `loadtest/results/results.csv`.

---

## 8. Referências

1. W3C. *SOAP Version 1.2 Part 1: Messaging Framework (Second Edition)*. https://www.w3.org/TR/soap12/
2. Fielding, R. T. *Architectural Styles and the Design of Network-Based Software Architectures*. Doctoral Dissertation, University of California, Irvine, 2000. https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm
3. *REST API Tutorial*. https://restfulapi.net/
4. *GraphQL: A query language for your API*. https://graphql.org/
5. *gRPC: A high performance, open source universal RPC framework*. https://grpc.io/
6. Stowe, M. *XML, SOAP, JSON, REST, GraphQL?*. https://www.slideshare.net/mikestowe/xml-soap-json-rest-graphql
7. Brito, G., Valente, M. T. *REST vs GraphQL: A Controlled Experiment*. In Proc. of the Int. Conf. Software Architecture (ICSA), 2020. https://www.researchgate.net/publication/339413273_REST_vs_GraphQL_A_Controlled_Experiment
