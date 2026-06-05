/*
 * Serviço de Streaming de Músicas — versão SOAP (Node.js / pacote `soap`).
 *
 * SOAP 1.1 sobre HTTP, contrato WSDL (gerado em wsdl.js). Expõe as mesmas 18
 * operações da versão SOAP em Python (spyne). WSDL acessível em /wsdl?wsdl.
 *
 * Rodar:  node server.js        (porta 8104)
 */
'use strict';

const http = require('http');
const soap = require('soap');
const { store, NotFound } = require('../common/store');
const { buildWsdl } = require('./wsdl');

const PORT = Number(process.env.PORT || 8104);
const LOCATION = `http://127.0.0.1:${PORT}/wsdl`;
const wsdlXml = buildWsdl(LOCATION);

// Helpers de conversão para a forma esperada pelo WSDL (arrays nomeados).
const arrUser = (xs) => ({ User: xs });
const arrMusic = (xs) => ({ Music: xs });
const arrPlaylist = (xs) => ({ Playlist: xs.map(plOut) });
const plOut = (p) => ({ ...p, musicaIds: { int: p.musicaIds } });

// musicaIds chega do parser como { int: [..] } ou { int: '5' }; normaliza.
function parseIds(musicaIds) {
  if (!musicaIds || musicaIds.int === undefined) return [];
  const v = musicaIds.int;
  return (Array.isArray(v) ? v : [v]).map(Number);
}

function guard(fn) {
  return (args) => {
    try {
      return fn(args);
    } catch (e) {
      if (e instanceof NotFound) {
        throw { Fault: { Code: { Value: 'soap:Client' }, Reason: { Text: e.message } } };
      }
      throw e;
    }
  };
}

const service = {
  StreamingService: {
    StreamingPort: {
      // ---- Usuários ----
      listUsers: () => ({ listUsersResult: arrUser(store.listUsers()) }),
      getUser: guard((a) => ({ getUserResult: store.getUser(a.id) })),
      createUser: (a) => ({ createUserResult: store.createUser(a.nome, a.idade) }),
      updateUser: guard((a) => ({ updateUserResult: store.updateUser(a.id, a.nome, a.idade) })),
      deleteUser: guard((a) => { store.deleteUser(a.id); return { deleteUserResult: 'ok' }; }),

      // ---- Músicas ----
      listMusics: () => ({ listMusicsResult: arrMusic(store.listMusics()) }),
      getMusic: guard((a) => ({ getMusicResult: store.getMusic(a.id) })),
      createMusic: (a) => ({ createMusicResult: store.createMusic(a.nome, a.artista, a.ano, a.album) }),
      updateMusic: guard((a) => ({ updateMusicResult: store.updateMusic(a.id, a.nome, a.artista, a.ano, a.album) })),
      deleteMusic: guard((a) => { store.deleteMusic(a.id); return { deleteMusicResult: 'ok' }; }),

      // ---- Playlists ----
      listPlaylists: () => ({ listPlaylistsResult: arrPlaylist(store.listPlaylists()) }),
      getPlaylist: guard((a) => ({ getPlaylistResult: plOut(store.getPlaylist(a.id)) })),
      createPlaylist: (a) => ({ createPlaylistResult: plOut(store.createPlaylist(a.nome, a.usuarioId, parseIds(a.musicaIds))) }),
      updatePlaylist: guard((a) => ({ updatePlaylistResult: plOut(store.updatePlaylist(a.id, a.nome, a.usuarioId, a.musicaIds ? parseIds(a.musicaIds) : null)) })),
      deletePlaylist: guard((a) => { store.deletePlaylist(a.id); return { deletePlaylistResult: 'ok' }; }),

      // ---- Consultas relacionais ----
      playlistsByUser: (a) => ({ playlistsByUserResult: arrPlaylist(store.playlistsByUser(a.userId)) }),
      musicsByPlaylist: guard((a) => ({ musicsByPlaylistResult: arrMusic(store.musicsByPlaylist(a.playlistId)) })),
      playlistsByMusic: (a) => ({ playlistsByMusicResult: arrPlaylist(store.playlistsByMusic(a.musicId)) }),
    },
  },
};

const server = http.createServer((req, res) => {
  res.statusCode = 404;
  res.end('404: SOAP em /wsdl');
});

server.listen(PORT, () => {
  soap.listen(server, '/wsdl', service, wsdlXml, () => {
    console.log(`[SOAP/Node] ouvindo em http://127.0.0.1:${PORT}/wsdl (WSDL em /wsdl?wsdl)`);
  });
});
