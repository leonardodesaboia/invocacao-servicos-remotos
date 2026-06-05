"""
Serviço de Streaming de Músicas — versão gRPC (Python / grpcio).

Contrato definido em proto/streaming.proto. A comunicação usa HTTP/2 +
Protocol Buffers (binário). Os métodos do serviço espelham o CRUD dos 3
recursos e as 5 consultas relacionais.

Rodar:  python server.py        (porta 8003)
"""
import os
import sys
from concurrent import futures

import grpc

_HERE = os.path.dirname(__file__)
sys.path.insert(0, _HERE)                      # para achar streaming_pb2*
sys.path.insert(0, os.path.join(_HERE, ".."))  # para achar common

import streaming_pb2 as pb        # noqa: E402
import streaming_pb2_grpc as pbg  # noqa: E402
from common.store import store, NotFound  # noqa: E402

PORT = int(os.environ.get("PORT", 8003))


def to_user(u):
    return pb.User(id=u["id"], nome=u["nome"], idade=u["idade"])


def to_music(m):
    return pb.Music(id=m["id"], nome=m["nome"], artista=m["artista"],
                    ano=m["ano"], album=m["album"])


def to_playlist(p):
    return pb.Playlist(id=p["id"], nome=p["nome"], usuarioId=p["usuarioId"],
                       musicaIds=p["musicaIds"])


class StreamingServicer(pbg.StreamingServiceServicer):
    # ---- Usuários ----
    def ListUsers(self, request, context):
        return pb.Users(users=[to_user(u) for u in store.list_users()])

    def GetUser(self, request, context):
        try:
            return to_user(store.get_user(request.id))
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def CreateUser(self, request, context):
        return to_user(store.create_user(request.nome, request.idade))

    def UpdateUser(self, request, context):
        try:
            return to_user(store.update_user(request.id, request.nome, request.idade))
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def DeleteUser(self, request, context):
        try:
            store.delete_user(request.id)
            return pb.Empty()
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    # ---- Músicas ----
    def ListMusics(self, request, context):
        return pb.Musics(musics=[to_music(m) for m in store.list_musics()])

    def GetMusic(self, request, context):
        try:
            return to_music(store.get_music(request.id))
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def CreateMusic(self, request, context):
        return to_music(store.create_music(request.nome, request.artista,
                                           request.ano, request.album))

    def UpdateMusic(self, request, context):
        try:
            return to_music(store.update_music(request.id, request.nome,
                                               request.artista, request.ano,
                                               request.album))
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def DeleteMusic(self, request, context):
        try:
            store.delete_music(request.id)
            return pb.Empty()
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    # ---- Playlists ----
    def ListPlaylists(self, request, context):
        return pb.Playlists(playlists=[to_playlist(p) for p in store.list_playlists()])

    def GetPlaylist(self, request, context):
        try:
            return to_playlist(store.get_playlist(request.id))
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def CreatePlaylist(self, request, context):
        return to_playlist(store.create_playlist(request.nome, request.usuarioId,
                                                 list(request.musicaIds)))

    def UpdatePlaylist(self, request, context):
        try:
            mids = list(request.musicaIds) if request.musicaIds else None
            return to_playlist(store.update_playlist(request.id, request.nome,
                                                     request.usuarioId, mids))
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def DeletePlaylist(self, request, context):
        try:
            store.delete_playlist(request.id)
            return pb.Empty()
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    # ---- Consultas relacionais ----
    def PlaylistsByUser(self, request, context):
        return pb.Playlists(playlists=[to_playlist(p) for p in store.playlists_by_user(request.id)])

    def MusicsByPlaylist(self, request, context):
        try:
            return pb.Musics(musics=[to_music(m) for m in store.musics_by_playlist(request.id)])
        except NotFound as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def PlaylistsByMusic(self, request, context):
        return pb.Playlists(playlists=[to_playlist(p) for p in store.playlists_by_music(request.id)])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    pbg.add_StreamingServiceServicer_to_server(StreamingServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{PORT}")
    server.start()
    print(f"[gRPC/Python] ouvindo em 127.0.0.1:{PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
