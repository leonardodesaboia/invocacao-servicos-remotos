"""
Serviço de Streaming de Músicas — versão REST (Python / Flask).

Expõe o CRUD dos 3 recursos (usuários, músicas, playlists) seguindo o estilo
REST: recursos identificados por URL, verbos HTTP (GET/POST/PUT/DELETE) e
representação em JSON. As 5 consultas relacionais são sub-recursos.

Rodar:  python server.py        (porta 8001)
"""
import os
import sys

from flask import Flask, jsonify, request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.store import store, NotFound  # noqa: E402

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8001))


@app.errorhandler(NotFound)
def _nf(e):
    return jsonify({"error": str(e)}), 404


# ---------------- Usuários ----------------
@app.get("/users")
def list_users():
    return jsonify(store.list_users())


@app.get("/users/<int:uid>")
def get_user(uid):
    return jsonify(store.get_user(uid))


@app.post("/users")
def create_user():
    b = request.get_json(force=True)
    u = store.create_user(b["nome"], b.get("idade", 0))
    return jsonify(u), 201


@app.put("/users/<int:uid>")
def update_user(uid):
    b = request.get_json(force=True)
    return jsonify(store.update_user(uid, b.get("nome"), b.get("idade")))


@app.delete("/users/<int:uid>")
def delete_user(uid):
    store.delete_user(uid)
    return "", 204


# ---------------- Músicas ----------------
@app.get("/musics")
def list_musics():
    return jsonify(store.list_musics())


@app.get("/musics/<int:mid>")
def get_music(mid):
    return jsonify(store.get_music(mid))


@app.post("/musics")
def create_music():
    b = request.get_json(force=True)
    m = store.create_music(b["nome"], b["artista"], b.get("ano", 0), b.get("album", ""))
    return jsonify(m), 201


@app.put("/musics/<int:mid>")
def update_music(mid):
    b = request.get_json(force=True)
    return jsonify(store.update_music(mid, b.get("nome"), b.get("artista"),
                                      b.get("ano"), b.get("album")))


@app.delete("/musics/<int:mid>")
def delete_music(mid):
    store.delete_music(mid)
    return "", 204


# ---------------- Playlists ----------------
@app.get("/playlists")
def list_playlists():
    return jsonify(store.list_playlists())


@app.get("/playlists/<int:pid>")
def get_playlist(pid):
    return jsonify(store.get_playlist(pid))


@app.post("/playlists")
def create_playlist():
    b = request.get_json(force=True)
    p = store.create_playlist(b["nome"], b["usuarioId"], b.get("musicaIds", []))
    return jsonify(p), 201


@app.put("/playlists/<int:pid>")
def update_playlist(pid):
    b = request.get_json(force=True)
    return jsonify(store.update_playlist(pid, b.get("nome"), b.get("usuarioId"),
                                         b.get("musicaIds")))


@app.delete("/playlists/<int:pid>")
def delete_playlist(pid):
    store.delete_playlist(pid)
    return "", 204


# ---------- Consultas relacionais (as 5 do enunciado) ----------
@app.get("/users/<int:uid>/playlists")
def playlists_by_user(uid):
    return jsonify(store.playlists_by_user(uid))


@app.get("/playlists/<int:pid>/musics")
def musics_by_playlist(pid):
    return jsonify(store.musics_by_playlist(pid))


@app.get("/musics/<int:mid>/playlists")
def playlists_by_music(mid):
    return jsonify(store.playlists_by_music(mid))


if __name__ == "__main__":
    print(f"[REST/Python] ouvindo em http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
