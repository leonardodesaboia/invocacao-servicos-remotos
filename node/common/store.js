/*
 * Store em memória compartilhado por TODOS os serviços Node.js (REST, GraphQL,
 * gRPC, SOAP). Carrega o seed.json e implementa o CRUD dos 3 recursos
 * (usuários, músicas, playlists) e as 5 consultas relacionais do enunciado.
 *
 * Espelha exatamente a lógica do store Python (python/common/store.py): a única
 * coisa que muda entre as versões é a CAMADA DE INVOCAÇÃO REMOTA.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const SEED = path.join(__dirname, '..', '..', 'data', 'seed.json');

class NotFound extends Error {}

class Store {
  constructor(seedPath = SEED) {
    const data = JSON.parse(fs.readFileSync(seedPath, 'utf-8'));
    this.users = new Map(data.users.map((u) => [u.id, { ...u }]));
    this.musics = new Map(data.musics.map((m) => [m.id, { ...m }]));
    this.playlists = new Map(data.playlists.map((p) => [p.id, { ...p }]));
    const meta = data._meta || {};
    this._nextUser = meta.nextUserId || this.users.size + 1;
    this._nextMusic = meta.nextMusicId || this.musics.size + 1;
    this._nextPlaylist = meta.nextPlaylistId || this.playlists.size + 1;
  }

  // ---------- Usuários ----------
  listUsers() {
    return [...this.users.values()].map((u) => ({ ...u }));
  }

  getUser(id) {
    const u = this.users.get(Number(id));
    if (!u) throw new NotFound(`usuario ${id} nao encontrado`);
    return { ...u };
  }

  createUser(nome, idade) {
    const id = this._nextUser++;
    const u = { id, nome, idade: Number(idade) || 0 };
    this.users.set(id, u);
    return { ...u };
  }

  updateUser(id, nome, idade) {
    id = Number(id);
    const u = this.users.get(id);
    if (!u) throw new NotFound(`usuario ${id} nao encontrado`);
    if (nome !== undefined && nome !== null) u.nome = nome;
    if (idade !== undefined && idade !== null) u.idade = Number(idade);
    return { ...u };
  }

  deleteUser(id) {
    id = Number(id);
    if (!this.users.has(id)) throw new NotFound(`usuario ${id} nao encontrado`);
    this.users.delete(id);
  }

  // ---------- Músicas ----------
  listMusics() {
    return [...this.musics.values()].map((m) => ({ ...m }));
  }

  getMusic(id) {
    const m = this.musics.get(Number(id));
    if (!m) throw new NotFound(`musica ${id} nao encontrada`);
    return { ...m };
  }

  createMusic(nome, artista, ano = 0, album = '') {
    const id = this._nextMusic++;
    const m = { id, nome, artista, ano: Number(ano) || 0, album: album || '' };
    this.musics.set(id, m);
    return { ...m };
  }

  updateMusic(id, nome, artista, ano, album) {
    id = Number(id);
    const m = this.musics.get(id);
    if (!m) throw new NotFound(`musica ${id} nao encontrada`);
    if (nome !== undefined && nome !== null) m.nome = nome;
    if (artista !== undefined && artista !== null) m.artista = artista;
    if (ano !== undefined && ano !== null) m.ano = Number(ano);
    if (album !== undefined && album !== null) m.album = album;
    return { ...m };
  }

  deleteMusic(id) {
    id = Number(id);
    if (!this.musics.has(id)) throw new NotFound(`musica ${id} nao encontrada`);
    this.musics.delete(id);
    for (const p of this.playlists.values()) {
      if (p.musicaIds.includes(id)) {
        p.musicaIds = p.musicaIds.filter((x) => x !== id);
      }
    }
  }

  // ---------- Playlists ----------
  listPlaylists() {
    return [...this.playlists.values()].map((p) => ({ ...p, musicaIds: [...p.musicaIds] }));
  }

  getPlaylist(id) {
    const p = this.playlists.get(Number(id));
    if (!p) throw new NotFound(`playlist ${id} nao encontrada`);
    return { ...p, musicaIds: [...p.musicaIds] };
  }

  createPlaylist(nome, usuarioId, musicaIds = []) {
    const id = this._nextPlaylist++;
    const p = { id, nome, usuarioId: Number(usuarioId), musicaIds: [...(musicaIds || [])].map(Number) };
    this.playlists.set(id, p);
    return { ...p, musicaIds: [...p.musicaIds] };
  }

  updatePlaylist(id, nome, usuarioId, musicaIds) {
    id = Number(id);
    const p = this.playlists.get(id);
    if (!p) throw new NotFound(`playlist ${id} nao encontrada`);
    if (nome !== undefined && nome !== null) p.nome = nome;
    if (usuarioId !== undefined && usuarioId !== null) p.usuarioId = Number(usuarioId);
    if (musicaIds !== undefined && musicaIds !== null) p.musicaIds = [...musicaIds].map(Number);
    return { ...p, musicaIds: [...p.musicaIds] };
  }

  deletePlaylist(id) {
    id = Number(id);
    if (!this.playlists.has(id)) throw new NotFound(`playlist ${id} nao encontrada`);
    this.playlists.delete(id);
  }

  // ---------- Consultas relacionais (as 5 do enunciado) ----------
  playlistsByUser(userId) {
    userId = Number(userId);
    return [...this.playlists.values()]
      .filter((p) => p.usuarioId === userId)
      .map((p) => ({ ...p, musicaIds: [...p.musicaIds] }));
  }

  musicsByPlaylist(playlistId) {
    playlistId = Number(playlistId);
    const p = this.playlists.get(playlistId);
    if (!p) throw new NotFound(`playlist ${playlistId} nao encontrada`);
    return p.musicaIds
      .filter((mid) => this.musics.has(mid))
      .map((mid) => ({ ...this.musics.get(mid) }));
  }

  playlistsByMusic(musicId) {
    musicId = Number(musicId);
    return [...this.playlists.values()]
      .filter((p) => p.musicaIds.includes(musicId))
      .map((p) => ({ ...p, musicaIds: [...p.musicaIds] }));
  }
}

module.exports = { Store, NotFound, store: new Store() };
