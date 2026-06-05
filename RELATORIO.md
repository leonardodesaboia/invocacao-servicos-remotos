# Trabalho 6 - Comparacao de Tecnologias de Invocacao de Servicos Remotos

## 1. Identificacao

Disciplina: Computacao Distribuida  
Professor: Nabor C. Mendonca  
Equipe: preencher com os nomes dos integrantes

## 2. Objetivo

O trabalho compara quatro tecnologias de invocacao remota: SOAP, REST, GraphQL e gRPC. Para tornar a comparacao concreta, foi implementado o mesmo servico de streaming de musicas em todas elas, mantendo os mesmos dados, operacoes e regras de negocio.

O servico gerencia tres recursos:

- Usuarios: `id`, `nome`, `idade`
- Musicas: `id`, `nome`, `artista`, `ano`, `album`
- Playlists: `id`, `nome`, `usuarioId`, `musicaIds`

Todas as versoes oferecem CRUD completo e as consultas relacionais exigidas no enunciado:

- listar todos os usuarios;
- listar todas as musicas;
- listar playlists de um usuario;
- listar musicas de uma playlist;
- listar playlists que contem uma musica.

## 3. Tecnologias

### SOAP

SOAP e um protocolo baseado em XML, padronizado pelo W3C. Ele define envelope, corpo da mensagem, contrato WSDL e regras formais para troca de mensagens.

Vantagens:

- contrato forte via WSDL;
- bom suporte a ambientes corporativos e sistemas legados;
- padroes maduros para seguranca e interoperabilidade.

Desvantagens:

- mensagens XML verbosas;
- maior custo de serializacao e parsing;
- implementacao mais pesada e menos simples para APIs modernas.

### REST

REST e um estilo arquitetural baseado em recursos, URIs, verbos HTTP e representacoes como JSON. E amplamente usado em APIs web.

Vantagens:

- simples de entender, testar e consumir;
- usa diretamente recursos do HTTP;
- bom equilibrio entre desempenho, produtividade e interoperabilidade.

Desvantagens:

- nao possui contrato unico obrigatorio;
- pode exigir varias requisicoes para buscar dados relacionados;
- depende de disciplina de projeto para manter padronizacao.

### GraphQL

GraphQL e uma linguagem de consulta para APIs. O cliente envia uma query declarando exatamente quais campos deseja receber.

Vantagens:

- evita overfetching e underfetching;
- permite buscar dados relacionados em uma unica requisicao;
- schema tipado facilita documentacao e evolucao da API.

Desvantagens:

- maior overhead de parse e execucao da query;
- cache HTTP tradicional e menos direto;
- pode gerar consultas caras se nao houver controle.

### gRPC

gRPC e um framework de RPC de alto desempenho que usa HTTP/2 e Protocol Buffers.

Vantagens:

- comunicacao binaria eficiente;
- contrato forte via `.proto`;
- excelente desempenho e suporte a streaming.

Desvantagens:

- menos conveniente para teste manual em navegador;
- exige geracao ou carregamento de stubs;
- integracao com clientes web comuns e menos direta que REST.

## 4. Implementacao

O projeto implementa 8 versoes do mesmo servico:

| Linguagem | REST | GraphQL | gRPC | SOAP |
|---|---|---|---|---|
| Python | Sim | Sim | Sim | Sim |
| Node.js | Sim | Sim | Sim | Sim |

A persistencia e em memoria. Todas as versoes carregam o mesmo `data/seed.json`, com 300 usuarios, 500 musicas e 200 playlists.

A regra de negocio foi concentrada em:

- `python/common/store.py`
- `node/common/store.js`

Assim, a comparacao fica focada na camada de invocacao remota, e nao em diferencas de regra de negocio.

## 5. Testes de carga

Os testes estao em `loadtest/loadtest.py`. Eles executam cada servidor isoladamente, aplicam diferentes niveis de concorrencia e registram vazao, latencia media, p50, p95, quantidade de requisicoes e erros.

Foram medidas duas operacoes:

- `listMusics`: retorna 500 musicas, representando payload maior.
- `musicsByPlaylist`: retorna as musicas de uma playlist, representando payload menor.

Os resultados completos estao em:

- `loadtest/results/results.csv`
- `loadtest/results/*.png`

## 6. Analise dos resultados

Nos resultados coletados, gRPC apresentou o melhor desempenho geral, principalmente na versao Node.js. Em `musicsByPlaylist` com 100 usuarios simultaneos, gRPC/Node atingiu cerca de 8864 req/s, enquanto gRPC/Python atingiu cerca de 3731 req/s.

REST teve desempenho intermediario e boa estabilidade. A versao Node.js manteve vazao acima de 1000 req/s em varios cenarios, com zero erros nos testes registrados.

GraphQL apresentou overhead maior, especialmente em Python. Apesar disso, sua principal vantagem aparece quando o cliente precisa consultar dados relacionados em uma unica chamada, escolhendo exatamente os campos retornados.

SOAP foi o mais pesado em geral, especialmente em Python, por causa do XML, envelope SOAP, WSDL e validacao. A versao Node.js teve desempenho melhor que a Python nos resultados registrados, mas ainda carrega a complexidade caracteristica da tecnologia.

Tambem foi observado que os servidores HTTP Python usam servidores de desenvolvimento. Em cargas altas, isso gerou erros em alguns cenarios, principalmente REST/Python e GraphQL/Python. Essa limitacao deve ser considerada na analise, pois em producao seria adequado usar servidores como Gunicorn, Waitress ou outra solucao mais robusta.

## 7. Conclusao

A comparacao mostra que a melhor tecnologia depende do contexto:

- gRPC e a melhor escolha quando desempenho, contrato forte e comunicacao eficiente entre servicos sao prioridade.
- REST e a opcao mais equilibrada para APIs web simples, interoperaveis e faceis de consumir.
- GraphQL e vantajoso quando o cliente precisa controlar a forma dos dados e reduzir multiplas chamadas.
- SOAP ainda faz sentido em ambientes corporativos ou legados que dependem de WSDL e padroes formais, mas tem maior custo e complexidade.

Para o servico implementado, gRPC apresentou os melhores resultados de carga, REST teve o melhor equilibrio geral, GraphQL trouxe flexibilidade de consulta e SOAP demonstrou maior overhead.
