"""
Store em memória compartilhado por TODOS os serviços Python (REST, GraphQL,
gRPC, SOAP). Carrega o seed.json e implementa o CRUD dos 3 recursos
(usuários, músicas, playlists) e as 5 consultas relacionais do enunciado.

Como todos os serviços usam exatamente este mesmo store, a lógica de negócio
e a persistência (em memória) são idênticas entre as tecnologias — o que muda
de uma versão para outra é apenas a CAMADA DE INVOCAÇÃO REMOTA.
"""
import json
import os
import threading

_SEED = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed.json")


class NotFound(Exception):
    """Recurso inexistente."""
    pass


class Store:
    def __init__(self, seed_path=_SEED):
        self._lock = threading.RLock()
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.users = {u["id"]: dict(u) for u in data["users"]}
        self.musics = {m["id"]: dict(m) for m in data["musics"]}
        self.playlists = {p["id"]: dict(p) for p in data["playlists"]}
        meta = data.get("_meta", {})
        self._next_user = meta.get("nextUserId", max(self.users, default=0) + 1)
        self._next_music = meta.get("nextMusicId", max(self.musics, default=0) + 1)
        self._next_playlist = meta.get("nextPlaylistId", max(self.playlists, default=0) + 1)

    # ---------- Usuários ----------
    def list_users(self):
        with self._lock:
            return [dict(u) for u in self.users.values()]

    def get_user(self, uid):
        with self._lock:
            u = self.users.get(int(uid))
            if u is None:
                raise NotFound(f"usuario {uid} nao encontrado")
            return dict(u)

    def create_user(self, nome, idade):
        with self._lock:
            uid = self._next_user
            self._next_user += 1
            u = {"id": uid, "nome": nome, "idade": int(idade)}
            self.users[uid] = u
            return dict(u)

    def update_user(self, uid, nome=None, idade=None):
        with self._lock:
            uid = int(uid)
            if uid not in self.users:
                raise NotFound(f"usuario {uid} nao encontrado")
            u = self.users[uid]
            if nome is not None:
                u["nome"] = nome
            if idade is not None:
                u["idade"] = int(idade)
            return dict(u)

    def delete_user(self, uid):
        with self._lock:
            uid = int(uid)
            if uid not in self.users:
                raise NotFound(f"usuario {uid} nao encontrado")
            del self.users[uid]

    # ---------- Músicas ----------
    def list_musics(self):
        with self._lock:
            return [dict(m) for m in self.musics.values()]

    def get_music(self, mid):
        with self._lock:
            m = self.musics.get(int(mid))
            if m is None:
                raise NotFound(f"musica {mid} nao encontrada")
            return dict(m)

    def create_music(self, nome, artista, ano=0, album=""):
        with self._lock:
            mid = self._next_music
            self._next_music += 1
            m = {"id": mid, "nome": nome, "artista": artista,
                 "ano": int(ano or 0), "album": album or ""}
            self.musics[mid] = m
            return dict(m)

    def update_music(self, mid, nome=None, artista=None, ano=None, album=None):
        with self._lock:
            mid = int(mid)
            if mid not in self.musics:
                raise NotFound(f"musica {mid} nao encontrada")
            m = self.musics[mid]
            if nome is not None:
                m["nome"] = nome
            if artista is not None:
                m["artista"] = artista
            if ano is not None:
                m["ano"] = int(ano)
            if album is not None:
                m["album"] = album
            return dict(m)

    def delete_music(self, mid):
        with self._lock:
            mid = int(mid)
            if mid not in self.musics:
                raise NotFound(f"musica {mid} nao encontrada")
            del self.musics[mid]
            # remove a música de todas as playlists
            for p in self.playlists.values():
                if mid in p["musicaIds"]:
                    p["musicaIds"] = [x for x in p["musicaIds"] if x != mid]

    # ---------- Playlists ----------
    def list_playlists(self):
        with self._lock:
            return [dict(p) for p in self.playlists.values()]

    def get_playlist(self, pid):
        with self._lock:
            p = self.playlists.get(int(pid))
            if p is None:
                raise NotFound(f"playlist {pid} nao encontrada")
            return dict(p)

    def create_playlist(self, nome, usuario_id, musica_ids=None):
        with self._lock:
            pid = self._next_playlist
            self._next_playlist += 1
            p = {"id": pid, "nome": nome, "usuarioId": int(usuario_id),
                 "musicaIds": list(musica_ids or [])}
            self.playlists[pid] = p
            return dict(p)

    def update_playlist(self, pid, nome=None, usuario_id=None, musica_ids=None):
        with self._lock:
            pid = int(pid)
            if pid not in self.playlists:
                raise NotFound(f"playlist {pid} nao encontrada")
            p = self.playlists[pid]
            if nome is not None:
                p["nome"] = nome
            if usuario_id is not None:
                p["usuarioId"] = int(usuario_id)
            if musica_ids is not None:
                p["musicaIds"] = list(musica_ids)
            return dict(p)

    def delete_playlist(self, pid):
        with self._lock:
            pid = int(pid)
            if pid not in self.playlists:
                raise NotFound(f"playlist {pid} nao encontrada")
            del self.playlists[pid]

    # ---------- Consultas relacionais (as 5 do enunciado) ----------
    def playlists_by_user(self, uid):
        with self._lock:
            uid = int(uid)
            return [dict(p) for p in self.playlists.values() if p["usuarioId"] == uid]

    def musics_by_playlist(self, pid):
        with self._lock:
            pid = int(pid)
            p = self.playlists.get(pid)
            if p is None:
                raise NotFound(f"playlist {pid} nao encontrada")
            return [dict(self.musics[mid]) for mid in p["musicaIds"] if mid in self.musics]

    def playlists_by_music(self, mid):
        with self._lock:
            mid = int(mid)
            return [dict(p) for p in self.playlists.values() if mid in p["musicaIds"]]


# instância única por processo
store = Store()
