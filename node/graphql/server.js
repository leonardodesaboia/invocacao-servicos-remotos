/*
 * Serviço de Streaming de Músicas — versão GraphQL (Node.js / graphql-http).
 *
 * Endpoint único (/graphql) com schema fortemente tipado. O cliente escolhe os
 * campos e pode navegar pelas relações (usuário -> playlists -> músicas) em uma
 * só requisição. Espelha o schema da versão Python (Ariadne).
 *
 * Rodar:  node server.js        (porta 8102)
 */
'use strict';

const express = require('express');
const { createHandler } = require('graphql-http/lib/use/express');
const { buildSchema } = require('graphql');
const { store } = require('../common/store');

const PORT = Number(process.env.PORT || 8102);

const schema = buildSchema(`
  type User { id: Int!, nome: String!, idade: Int!, playlists: [Playlist!]! }
  type Music { id: Int!, nome: String!, artista: String!, ano: Int!, album: String!, playlists: [Playlist!]! }
  type Playlist { id: Int!, nome: String!, usuarioId: Int!, usuario: User, musicas: [Music!]! }

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
`);

// Resolvers de relações: anexamos funções aos objetos retornados.
function decorateUser(u) {
  return { ...u, playlists: () => store.playlistsByUser(u.id).map(decoratePlaylist) };
}
function decorateMusic(m) {
  return { ...m, playlists: () => store.playlistsByMusic(m.id).map(decoratePlaylist) };
}
function decoratePlaylist(p) {
  return {
    ...p,
    usuario: () => { try { return decorateUser(store.getUser(p.usuarioId)); } catch { return null; } },
    musicas: () => store.musicsByPlaylist(p.id).map(decorateMusic),
  };
}

const root = {
  users: () => store.listUsers().map(decorateUser),
  user: ({ id }) => { try { return decorateUser(store.getUser(id)); } catch { return null; } },
  musics: () => store.listMusics().map(decorateMusic),
  music: ({ id }) => { try { return decorateMusic(store.getMusic(id)); } catch { return null; } },
  playlists: () => store.listPlaylists().map(decoratePlaylist),
  playlist: ({ id }) => { try { return decoratePlaylist(store.getPlaylist(id)); } catch { return null; } },
  playlistsByUser: ({ userId }) => store.playlistsByUser(userId).map(decoratePlaylist),
  musicsByPlaylist: ({ playlistId }) => store.musicsByPlaylist(playlistId).map(decorateMusic),
  playlistsByMusic: ({ musicId }) => store.playlistsByMusic(musicId).map(decoratePlaylist),

  createUser: ({ nome, idade }) => decorateUser(store.createUser(nome, idade)),
  updateUser: ({ id, nome, idade }) => decorateUser(store.updateUser(id, nome, idade)),
  deleteUser: ({ id }) => { store.deleteUser(id); return true; },
  createMusic: ({ nome, artista, ano, album }) => decorateMusic(store.createMusic(nome, artista, ano, album)),
  updateMusic: ({ id, nome, artista, ano, album }) => decorateMusic(store.updateMusic(id, nome, artista, ano, album)),
  deleteMusic: ({ id }) => { store.deleteMusic(id); return true; },
  createPlaylist: ({ nome, usuarioId, musicaIds }) => decoratePlaylist(store.createPlaylist(nome, usuarioId, musicaIds || [])),
  updatePlaylist: ({ id, nome, usuarioId, musicaIds }) => decoratePlaylist(store.updatePlaylist(id, nome, usuarioId, musicaIds)),
  deletePlaylist: ({ id }) => { store.deletePlaylist(id); return true; },
};

const app = express();
app.all('/graphql', createHandler({ schema, rootValue: root }));
app.listen(PORT, () => console.log(`[GraphQL/Node] ouvindo em http://127.0.0.1:${PORT}/graphql`));
