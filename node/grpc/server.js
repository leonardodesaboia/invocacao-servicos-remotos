/*
 * Serviço de Streaming de Músicas — versão gRPC (Node.js / @grpc/grpc-js).
 *
 * Carrega dinamicamente o MESMO contrato proto/streaming.proto usado pela
 * versão Python. Comunicação via HTTP/2 + Protocol Buffers.
 *
 * Rodar:  node server.js        (porta 8103)
 */
'use strict';

const path = require('path');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const { store, NotFound } = require('../common/store');

const PORT = Number(process.env.PORT || 8103);
const PROTO = path.join(__dirname, '..', '..', 'proto', 'streaming.proto');

const pkgDef = protoLoader.loadSync(PROTO, {
  keepCase: true,
  longs: Number,
  defaults: true,
  oneofs: true,
});
const proto = grpc.loadPackageDefinition(pkgDef).streaming;

function notFound(callback, e) {
  callback({ code: grpc.status.NOT_FOUND, message: e.message });
}

const impl = {
  // ---- Usuários ----
  ListUsers: (_, cb) => cb(null, { users: store.listUsers() }),
  GetUser: (call, cb) => { try { cb(null, store.getUser(call.request.id)); } catch (e) { notFound(cb, e); } },
  CreateUser: (call, cb) => cb(null, store.createUser(call.request.nome, call.request.idade)),
  UpdateUser: (call, cb) => { try { cb(null, store.updateUser(call.request.id, call.request.nome, call.request.idade)); } catch (e) { notFound(cb, e); } },
  DeleteUser: (call, cb) => { try { store.deleteUser(call.request.id); cb(null, {}); } catch (e) { notFound(cb, e); } },

  // ---- Músicas ----
  ListMusics: (_, cb) => cb(null, { musics: store.listMusics() }),
  GetMusic: (call, cb) => { try { cb(null, store.getMusic(call.request.id)); } catch (e) { notFound(cb, e); } },
  CreateMusic: (call, cb) => cb(null, store.createMusic(call.request.nome, call.request.artista, call.request.ano, call.request.album)),
  UpdateMusic: (call, cb) => { try { cb(null, store.updateMusic(call.request.id, call.request.nome, call.request.artista, call.request.ano, call.request.album)); } catch (e) { notFound(cb, e); } },
  DeleteMusic: (call, cb) => { try { store.deleteMusic(call.request.id); cb(null, {}); } catch (e) { notFound(cb, e); } },

  // ---- Playlists ----
  ListPlaylists: (_, cb) => cb(null, { playlists: store.listPlaylists() }),
  GetPlaylist: (call, cb) => { try { cb(null, store.getPlaylist(call.request.id)); } catch (e) { notFound(cb, e); } },
  CreatePlaylist: (call, cb) => cb(null, store.createPlaylist(call.request.nome, call.request.usuarioId, call.request.musicaIds || [])),
  UpdatePlaylist: (call, cb) => {
    try {
      const mids = call.request.musicaIds && call.request.musicaIds.length ? call.request.musicaIds : null;
      cb(null, store.updatePlaylist(call.request.id, call.request.nome, call.request.usuarioId, mids));
    } catch (e) { notFound(cb, e); }
  },
  DeletePlaylist: (call, cb) => { try { store.deletePlaylist(call.request.id); cb(null, {}); } catch (e) { notFound(cb, e); } },

  // ---- Consultas relacionais ----
  PlaylistsByUser: (call, cb) => cb(null, { playlists: store.playlistsByUser(call.request.id) }),
  MusicsByPlaylist: (call, cb) => { try { cb(null, { musics: store.musicsByPlaylist(call.request.id) }); } catch (e) { notFound(cb, e); } },
  PlaylistsByMusic: (call, cb) => cb(null, { playlists: store.playlistsByMusic(call.request.id) }),
};

const server = new grpc.Server();
server.addService(proto.StreamingService.service, impl);
server.bindAsync(`0.0.0.0:${PORT}`, grpc.ServerCredentials.createInsecure(), (err) => {
  if (err) { console.error(err); process.exit(1); }
  console.log(`[gRPC/Node] ouvindo em 127.0.0.1:${PORT}`);
});
