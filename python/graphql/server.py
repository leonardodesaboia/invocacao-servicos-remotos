"""
Serviço de Streaming de Músicas — versão GraphQL (Python / Ariadne).

Expõe um único endpoint (/graphql) com um schema fortemente tipado. O cliente
escolhe exatamente quais campos quer, e pode navegar pelas relações em uma
única requisição (ex.: usuário -> playlists -> músicas). As 5 consultas do
enunciado estão como queries e também como campos relacionais aninhados.

Rodar:  python server.py        (porta 8002)
"""
import os
import sys

from ariadne import (MutationType, ObjectType, QueryType, gql,
                      make_executable_schema)
from ariadne.wsgi import GraphQL

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.store import store, NotFound  # noqa: E402

PORT = int(os.environ.get("PORT", 8002))

type_defs = gql("""
    type User {
        id: Int!
        nome: String!
        idade: Int!
        playlists: [Playlist!]!
    }

    type Music {
        id: Int!
        nome: String!
        artista: String!
        ano: Int!
        album: String!
        playlists: [Playlist!]!
    }

    type Playlist {
        id: Int!
        nome: String!
        usuarioId: Int!
        usuario: User
        musicas: [Music!]!
    }

    type Query {
        users: [User!]!
        user(id: Int!): User
        musics: [Music!]!
        music(id: Int!): Music
        playlists: [Playlist!]!
        playlist(id: Int!): Playlist
        playlistsByUser(userId: Int!): [Playlist!]!
        musicsByPlaylist(playlistId: Int!): [Music!]!
        playlistsByMusic(musicId: Int!): [Playlist!]!
    }

    type Mutation {
        createUser(nome: String!, idade: Int!): User!
        updateUser(id: Int!, nome: String, idade: Int): User!
        deleteUser(id: Int!): Boolean!

        createMusic(nome: String!, artista: String!, ano: Int, album: String): Music!
        updateMusic(id: Int!, nome: String, artista: String, ano: Int, album: String): Music!
        deleteMusic(id: Int!): Boolean!

        createPlaylist(nome: String!, usuarioId: Int!, musicaIds: [Int!]): Playlist!
        updatePlaylist(id: Int!, nome: String, usuarioId: Int, musicaIds: [Int!]): Playlist!
        deletePlaylist(id: Int!): Boolean!
    }
""")

query = QueryType()
mutation = MutationType()
user_t = ObjectType("User")
music_t = ObjectType("Music")
playlist_t = ObjectType("Playlist")


# ---------- Queries ----------
@query.field("users")
def r_users(*_):
    return store.list_users()


@query.field("user")
def r_user(*_, id):
    try:
        return store.get_user(id)
    except NotFound:
        return None


@query.field("musics")
def r_musics(*_):
    return store.list_musics()


@query.field("music")
def r_music(*_, id):
    try:
        return store.get_music(id)
    except NotFound:
        return None


@query.field("playlists")
def r_playlists(*_):
    return store.list_playlists()


@query.field("playlist")
def r_playlist(*_, id):
    try:
        return store.get_playlist(id)
    except NotFound:
        return None


@query.field("playlistsByUser")
def r_pbu(*_, userId):
    return store.playlists_by_user(userId)


@query.field("musicsByPlaylist")
def r_mbp(*_, playlistId):
    return store.musics_by_playlist(playlistId)


@query.field("playlistsByMusic")
def r_pbm(*_, musicId):
    return store.playlists_by_music(musicId)


# ---------- Resolvers de relações ----------
@user_t.field("playlists")
def r_user_playlists(user, *_):
    return store.playlists_by_user(user["id"])


@music_t.field("playlists")
def r_music_playlists(music, *_):
    return store.playlists_by_music(music["id"])


@playlist_t.field("usuario")
def r_playlist_user(pl, *_):
    try:
        return store.get_user(pl["usuarioId"])
    except NotFound:
        return None


@playlist_t.field("musicas")
def r_playlist_musics(pl, *_):
    return store.musics_by_playlist(pl["id"])


# ---------- Mutations ----------
@mutation.field("createUser")
def m_cu(*_, nome, idade):
    return store.create_user(nome, idade)


@mutation.field("updateUser")
def m_uu(*_, id, nome=None, idade=None):
    return store.update_user(id, nome, idade)


@mutation.field("deleteUser")
def m_du(*_, id):
    store.delete_user(id)
    return True


@mutation.field("createMusic")
def m_cm(*_, nome, artista, ano=0, album=""):
    return store.create_music(nome, artista, ano, album)


@mutation.field("updateMusic")
def m_um(*_, id, nome=None, artista=None, ano=None, album=None):
    return store.update_music(id, nome, artista, ano, album)


@mutation.field("deleteMusic")
def m_dm(*_, id):
    store.delete_music(id)
    return True


@mutation.field("createPlaylist")
def m_cp(*_, nome, usuarioId, musicaIds=None):
    return store.create_playlist(nome, usuarioId, musicaIds or [])


@mutation.field("updatePlaylist")
def m_up(*_, id, nome=None, usuarioId=None, musicaIds=None):
    return store.update_playlist(id, nome, usuarioId, musicaIds)


@mutation.field("deletePlaylist")
def m_dp(*_, id):
    store.delete_playlist(id)
    return True


schema = make_executable_schema(type_defs, query, mutation, user_t, music_t, playlist_t)
application = GraphQL(schema)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server, WSGIServer
    from socketserver import ThreadingMixIn

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True

    print(f"[GraphQL/Python] ouvindo em http://127.0.0.1:{PORT}/graphql")
    httpd = make_server("0.0.0.0", PORT, application, server_class=ThreadingWSGIServer)
    httpd.serve_forever()
