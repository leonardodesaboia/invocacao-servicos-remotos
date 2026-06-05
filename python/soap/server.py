"""
Serviço de Streaming de Músicas — versão SOAP (Python / spyne).

Protocolo SOAP 1.1 sobre HTTP, com contrato WSDL gerado automaticamente
(acessível em http://127.0.0.1:8004/?wsdl). Mensagens em XML. Expõe o CRUD
dos 3 recursos e as 5 consultas relacionais como operações SOAP.

Rodar:  python server.py        (porta 8004)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import common.spyne_py312_fix  # noqa: E402,F401  (deve vir ANTES do spyne)

from spyne import (Application, Array, ComplexModel, Integer, ServiceBase,  # noqa: E402
                   Unicode, rpc)
from spyne.protocol.soap import Soap11  # noqa: E402
from spyne.server.wsgi import WsgiApplication  # noqa: E402

from common.store import store, NotFound  # noqa: E402

PORT = int(os.environ.get("PORT", 8004))
TNS = "streaming.soap"


# ---------------- Tipos (ComplexModel) ----------------
class User(ComplexModel):
    __namespace__ = TNS
    id = Integer
    nome = Unicode
    idade = Integer


class Music(ComplexModel):
    __namespace__ = TNS
    id = Integer
    nome = Unicode
    artista = Unicode
    ano = Integer
    album = Unicode


class Playlist(ComplexModel):
    __namespace__ = TNS
    id = Integer
    nome = Unicode
    usuarioId = Integer
    musicaIds = Array(Integer)


def mk_user(u):
    return User(id=u["id"], nome=u["nome"], idade=u["idade"])


def mk_music(m):
    return Music(id=m["id"], nome=m["nome"], artista=m["artista"],
                 ano=m["ano"], album=m["album"])


def mk_playlist(p):
    return Playlist(id=p["id"], nome=p["nome"], usuarioId=p["usuarioId"],
                    musicaIds=p["musicaIds"])


# ---------------- Serviço SOAP ----------------
class StreamingService(ServiceBase):
    # ---- Usuários ----
    @rpc(_returns=Array(User))
    def listUsers(ctx):
        return [mk_user(u) for u in store.list_users()]

    @rpc(Integer, _returns=User)
    def getUser(ctx, id):
        return mk_user(store.get_user(id))

    @rpc(Unicode, Integer, _returns=User)
    def createUser(ctx, nome, idade):
        return mk_user(store.create_user(nome, idade))

    @rpc(Integer, Unicode, Integer, _returns=User)
    def updateUser(ctx, id, nome, idade):
        return mk_user(store.update_user(id, nome, idade))

    @rpc(Integer, _returns=Unicode)
    def deleteUser(ctx, id):
        store.delete_user(id)
        return "ok"

    # ---- Músicas ----
    @rpc(_returns=Array(Music))
    def listMusics(ctx):
        return [mk_music(m) for m in store.list_musics()]

    @rpc(Integer, _returns=Music)
    def getMusic(ctx, id):
        return mk_music(store.get_music(id))

    @rpc(Unicode, Unicode, Integer, Unicode, _returns=Music)
    def createMusic(ctx, nome, artista, ano, album):
        return mk_music(store.create_music(nome, artista, ano, album))

    @rpc(Integer, Unicode, Unicode, Integer, Unicode, _returns=Music)
    def updateMusic(ctx, id, nome, artista, ano, album):
        return mk_music(store.update_music(id, nome, artista, ano, album))

    @rpc(Integer, _returns=Unicode)
    def deleteMusic(ctx, id):
        store.delete_music(id)
        return "ok"

    # ---- Playlists ----
    @rpc(_returns=Array(Playlist))
    def listPlaylists(ctx):
        return [mk_playlist(p) for p in store.list_playlists()]

    @rpc(Integer, _returns=Playlist)
    def getPlaylist(ctx, id):
        return mk_playlist(store.get_playlist(id))

    @rpc(Unicode, Integer, Array(Integer), _returns=Playlist)
    def createPlaylist(ctx, nome, usuarioId, musicaIds):
        return mk_playlist(store.create_playlist(nome, usuarioId, musicaIds or []))

    @rpc(Integer, Unicode, Integer, Array(Integer), _returns=Playlist)
    def updatePlaylist(ctx, id, nome, usuarioId, musicaIds):
        return mk_playlist(store.update_playlist(id, nome, usuarioId, musicaIds))

    @rpc(Integer, _returns=Unicode)
    def deletePlaylist(ctx, id):
        store.delete_playlist(id)
        return "ok"

    # ---- Consultas relacionais ----
    @rpc(Integer, _returns=Array(Playlist))
    def playlistsByUser(ctx, userId):
        return [mk_playlist(p) for p in store.playlists_by_user(userId)]

    @rpc(Integer, _returns=Array(Music))
    def musicsByPlaylist(ctx, playlistId):
        return [mk_music(m) for m in store.musics_by_playlist(playlistId)]

    @rpc(Integer, _returns=Array(Playlist))
    def playlistsByMusic(ctx, musicId):
        return [mk_playlist(p) for p in store.playlists_by_music(musicId)]


application = Application(
    [StreamingService],
    tns=TNS,
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIServer, make_server

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True

    print(f"[SOAP/Python] ouvindo em http://127.0.0.1:{PORT} (WSDL em /?wsdl)")
    httpd = make_server("0.0.0.0", PORT, wsgi_app, server_class=ThreadingWSGIServer)
    httpd.serve_forever()
