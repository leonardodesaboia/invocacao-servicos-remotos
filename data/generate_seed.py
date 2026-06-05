"""
Gerador de dados de seed para o Serviço de Streaming de Músicas.

Gera um arquivo `seed.json` com centenas de usuários, músicas e playlists,
usado de forma IDÊNTICA por todas as 8 versões do serviço (Python e Node.js,
nas 4 tecnologias). Isso garante que todas partam do mesmo estado inicial,
permitindo uma comparação justa nos testes de carga.

Uso:
    python generate_seed.py
"""
import json
import os
import random

random.seed(42)  # determinístico: todos rodam com os mesmos dados

N_USERS = 300
N_MUSICS = 500
N_PLAYLISTS = 200

PRIMEIROS = ["Ana", "Bruno", "Carla", "Diego", "Elena", "Felipe", "Gabriela",
             "Hugo", "Isabela", "João", "Karina", "Lucas", "Mariana", "Nuno",
             "Olivia", "Pedro", "Quésia", "Rafael", "Sofia", "Tiago", "Ursula",
             "Vitor", "Wesley", "Xavier", "Yara", "Zeca"]
SOBRENOMES = ["Silva", "Souza", "Costa", "Pereira", "Almeida", "Lima", "Gomes",
              "Ribeiro", "Carvalho", "Fernandes", "Rodrigues", "Martins",
              "Araújo", "Barbosa", "Rocha", "Dias", "Nascimento", "Moreira"]

ARTISTAS = ["The Killers", "Coldplay", "Radiohead", "Arctic Monkeys", "Muse",
            "Foo Fighters", "Linkin Park", "Queen", "Pink Floyd", "Nirvana",
            "Pearl Jam", "Red Hot Chili Peppers", "U2", "Oasis", "Blur",
            "Gorillaz", "Daft Punk", "Tame Impala", "The Strokes", "Interpol",
            "Legião Urbana", "Os Paralamas do Sucesso", "Titãs", "Skank",
            "Capital Inicial", "Charlie Brown Jr.", "Engenheiros do Hawaii"]

PALAVRAS_MUSICA = ["Mr Brightside", "Yellow", "Creep", "505", "Starlight",
                   "Everlong", "Numb", "Bohemian Rhapsody", "Time", "Lithium",
                   "Alive", "Californication", "One", "Wonderwall", "Song 2",
                   "Feel Good Inc", "Get Lucky", "The Less I Know", "Reptilia",
                   "Evil", "Tempo Perdido", "Lanterna dos Afogados", "Epitáfio",
                   "Garota Nacional", "Primeiros Erros", "Vento Ventania",
                   "Pais e Filhos", "Será", "Mais Uma Vez", "Toda Forma de Amor"]

PALAVRAS_PLAYLIST = ["Favoritas", "Treino", "Foco", "Relax", "Rock Nacional",
                     "Clássicos", "Indie", "Para Dormir", "Festa", "Estrada",
                     "Trabalho", "Domingo", "Anos 90", "Acústico", "Energia"]


def gerar():
    users = []
    for i in range(1, N_USERS + 1):
        nome = f"{random.choice(PRIMEIROS)} {random.choice(SOBRENOMES)}"
        users.append({"id": i, "nome": nome, "idade": random.randint(14, 70)})

    musics = []
    for i in range(1, N_MUSICS + 1):
        titulo = random.choice(PALAVRAS_MUSICA)
        artista = random.choice(ARTISTAS)
        musics.append({
            "id": i,
            "nome": titulo,
            "artista": artista,
            "ano": random.randint(1975, 2024),
            "album": f"{artista} - Vol. {random.randint(1, 5)}",
        })

    playlists = []
    for i in range(1, N_PLAYLISTS + 1):
        dono = random.randint(1, N_USERS)
        nome = f"{random.choice(PALAVRAS_PLAYLIST)} {random.randint(1, 99)}"
        qtd = random.randint(5, 25)
        musica_ids = sorted(random.sample(range(1, N_MUSICS + 1), qtd))
        playlists.append({
            "id": i,
            "nome": nome,
            "usuarioId": dono,
            "musicaIds": musica_ids,
        })

    return {
        "users": users,
        "musics": musics,
        "playlists": playlists,
        "_meta": {
            "nextUserId": N_USERS + 1,
            "nextMusicId": N_MUSICS + 1,
            "nextPlaylistId": N_PLAYLISTS + 1,
        },
    }


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "seed.json")
    data = gerar()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Gerado {out}")
    print(f"  usuarios : {len(data['users'])}")
    print(f"  musicas  : {len(data['musics'])}")
    print(f"  playlists: {len(data['playlists'])}")
