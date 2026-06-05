/*
 * Serviço de Streaming de Músicas — versão REST (Node.js / Express).
 *
 * Recursos identificados por URL, verbos HTTP (GET/POST/PUT/DELETE) e JSON.
 * As 5 consultas relacionais são expostas como sub-recursos.
 *
 * Rodar:  node server.js        (porta 8101)
 */
'use strict';

const express = require('express');
const { store, NotFound } = require('../common/store');

const app = express();
app.use(express.json());
const PORT = Number(process.env.PORT || 8101);

function wrap(handler) {
  return (req, res) => {
    try {
      handler(req, res);
    } catch (e) {
      if (e instanceof NotFound) res.status(404).json({ error: e.message });
      else res.status(500).json({ error: String(e) });
    }
  };
}

// ---------------- Usuários ----------------
app.get('/users', wrap((req, res) => res.json(store.listUsers())));
app.get('/users/:id', wrap((req, res) => res.json(store.getUser(req.params.id))));
app.post('/users', wrap((req, res) => res.status(201).json(store.createUser(req.body.nome, req.body.idade))));
app.put('/users/:id', wrap((req, res) => res.json(store.updateUser(req.params.id, req.body.nome, req.body.idade))));
app.delete('/users/:id', wrap((req, res) => { store.deleteUser(req.params.id); res.status(204).end(); }));

// ---------------- Músicas ----------------
app.get('/musics', wrap((req, res) => res.json(store.listMusics())));
app.get('/musics/:id', wrap((req, res) => res.json(store.getMusic(req.params.id))));
app.post('/musics', wrap((req, res) => res.status(201).json(
  store.createMusic(req.body.nome, req.body.artista, req.body.ano, req.body.album))));
app.put('/musics/:id', wrap((req, res) => res.json(
  store.updateMusic(req.params.id, req.body.nome, req.body.artista, req.body.ano, req.body.album))));
app.delete('/musics/:id', wrap((req, res) => { store.deleteMusic(req.params.id); res.status(204).end(); }));

// ---------------- Playlists ----------------
app.get('/playlists', wrap((req, res) => res.json(store.listPlaylists())));
app.get('/playlists/:id', wrap((req, res) => res.json(store.getPlaylist(req.params.id))));
app.post('/playlists', wrap((req, res) => res.status(201).json(
  store.createPlaylist(req.body.nome, req.body.usuarioId, req.body.musicaIds || []))));
app.put('/playlists/:id', wrap((req, res) => res.json(
  store.updatePlaylist(req.params.id, req.body.nome, req.body.usuarioId, req.body.musicaIds))));
app.delete('/playlists/:id', wrap((req, res) => { store.deletePlaylist(req.params.id); res.status(204).end(); }));

// ---------- Consultas relacionais (as 5 do enunciado) ----------
app.get('/users/:id/playlists', wrap((req, res) => res.json(store.playlistsByUser(req.params.id))));
app.get('/playlists/:id/musics', wrap((req, res) => res.json(store.musicsByPlaylist(req.params.id))));
app.get('/musics/:id/playlists', wrap((req, res) => res.json(store.playlistsByMusic(req.params.id))));

app.listen(PORT, () => console.log(`[REST/Node] ouvindo em http://127.0.0.1:${PORT}`));
