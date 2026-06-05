/*
 * Geração do WSDL (SOAP 1.1, document/literal) do serviço de streaming.
 *
 * Em vez de escrever ~600 linhas de XML à mão, descrevemos as operações em uma
 * pequena spec e geramos o WSDL programaticamente. Cobre as mesmas 18 operações
 * da versão SOAP em Python (spyne): CRUD dos 3 recursos + 5 consultas.
 */
'use strict';

const TNS = 'http://streaming.soap/';

// Cada operação: nome -> { params: [[nome, tipoXSD]...], result: tipoXSD }
// tipos: xsd:int, xsd:string, tns:ArrayOfInt, tns:User/Music/Playlist,
//        tns:ArrayOfUser/ArrayOfMusic/ArrayOfPlaylist
const OPS = {
  listUsers: { params: [], result: 'tns:ArrayOfUser' },
  getUser: { params: [['id', 'xsd:int']], result: 'tns:User' },
  createUser: { params: [['nome', 'xsd:string'], ['idade', 'xsd:int']], result: 'tns:User' },
  updateUser: { params: [['id', 'xsd:int'], ['nome', 'xsd:string'], ['idade', 'xsd:int']], result: 'tns:User' },
  deleteUser: { params: [['id', 'xsd:int']], result: 'xsd:string' },

  listMusics: { params: [], result: 'tns:ArrayOfMusic' },
  getMusic: { params: [['id', 'xsd:int']], result: 'tns:Music' },
  createMusic: { params: [['nome', 'xsd:string'], ['artista', 'xsd:string'], ['ano', 'xsd:int'], ['album', 'xsd:string']], result: 'tns:Music' },
  updateMusic: { params: [['id', 'xsd:int'], ['nome', 'xsd:string'], ['artista', 'xsd:string'], ['ano', 'xsd:int'], ['album', 'xsd:string']], result: 'tns:Music' },
  deleteMusic: { params: [['id', 'xsd:int']], result: 'xsd:string' },

  listPlaylists: { params: [], result: 'tns:ArrayOfPlaylist' },
  getPlaylist: { params: [['id', 'xsd:int']], result: 'tns:Playlist' },
  createPlaylist: { params: [['nome', 'xsd:string'], ['usuarioId', 'xsd:int'], ['musicaIds', 'tns:ArrayOfInt']], result: 'tns:Playlist' },
  updatePlaylist: { params: [['id', 'xsd:int'], ['nome', 'xsd:string'], ['usuarioId', 'xsd:int'], ['musicaIds', 'tns:ArrayOfInt']], result: 'tns:Playlist' },
  deletePlaylist: { params: [['id', 'xsd:int']], result: 'xsd:string' },

  playlistsByUser: { params: [['userId', 'xsd:int']], result: 'tns:ArrayOfPlaylist' },
  musicsByPlaylist: { params: [['playlistId', 'xsd:int']], result: 'tns:ArrayOfMusic' },
  playlistsByMusic: { params: [['musicId', 'xsd:int']], result: 'tns:ArrayOfPlaylist' },
};

function buildWsdl(location) {
  const elements = [];
  for (const [op, def] of Object.entries(OPS)) {
    const reqParts = def.params
      .map(([n, t]) => `<xsd:element name="${n}" type="${t}" minOccurs="0"/>`)
      .join('');
    elements.push(
      `<xsd:element name="${op}"><xsd:complexType><xsd:sequence>${reqParts}</xsd:sequence></xsd:complexType></xsd:element>`,
      `<xsd:element name="${op}Response"><xsd:complexType><xsd:sequence>` +
        `<xsd:element name="${op}Result" type="${def.result}" minOccurs="0"/>` +
        `</xsd:sequence></xsd:complexType></xsd:element>`
    );
  }

  const messages = [];
  const portOps = [];
  const bindOps = [];
  for (const op of Object.keys(OPS)) {
    messages.push(
      `<message name="${op}Request"><part name="parameters" element="tns:${op}"/></message>`,
      `<message name="${op}Response"><part name="parameters" element="tns:${op}Response"/></message>`
    );
    portOps.push(
      `<operation name="${op}"><input message="tns:${op}Request"/><output message="tns:${op}Response"/></operation>`
    );
    bindOps.push(
      `<operation name="${op}"><soap:operation soapAction="${op}"/>` +
        `<input><soap:body use="literal"/></input>` +
        `<output><soap:body use="literal"/></output></operation>`
    );
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="${TNS}"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="${TNS}">
  <types>
    <xsd:schema targetNamespace="${TNS}" elementFormDefault="qualified">
      <xsd:complexType name="User"><xsd:sequence>
        <xsd:element name="id" type="xsd:int"/>
        <xsd:element name="nome" type="xsd:string"/>
        <xsd:element name="idade" type="xsd:int"/>
      </xsd:sequence></xsd:complexType>
      <xsd:complexType name="Music"><xsd:sequence>
        <xsd:element name="id" type="xsd:int"/>
        <xsd:element name="nome" type="xsd:string"/>
        <xsd:element name="artista" type="xsd:string"/>
        <xsd:element name="ano" type="xsd:int"/>
        <xsd:element name="album" type="xsd:string"/>
      </xsd:sequence></xsd:complexType>
      <xsd:complexType name="Playlist"><xsd:sequence>
        <xsd:element name="id" type="xsd:int"/>
        <xsd:element name="nome" type="xsd:string"/>
        <xsd:element name="usuarioId" type="xsd:int"/>
        <xsd:element name="musicaIds" type="tns:ArrayOfInt"/>
      </xsd:sequence></xsd:complexType>
      <xsd:complexType name="ArrayOfInt"><xsd:sequence>
        <xsd:element name="int" type="xsd:int" minOccurs="0" maxOccurs="unbounded"/>
      </xsd:sequence></xsd:complexType>
      <xsd:complexType name="ArrayOfUser"><xsd:sequence>
        <xsd:element name="User" type="tns:User" minOccurs="0" maxOccurs="unbounded"/>
      </xsd:sequence></xsd:complexType>
      <xsd:complexType name="ArrayOfMusic"><xsd:sequence>
        <xsd:element name="Music" type="tns:Music" minOccurs="0" maxOccurs="unbounded"/>
      </xsd:sequence></xsd:complexType>
      <xsd:complexType name="ArrayOfPlaylist"><xsd:sequence>
        <xsd:element name="Playlist" type="tns:Playlist" minOccurs="0" maxOccurs="unbounded"/>
      </xsd:sequence></xsd:complexType>
      ${elements.join('\n      ')}
    </xsd:schema>
  </types>
  ${messages.join('\n  ')}
  <portType name="StreamingPort">
    ${portOps.join('\n    ')}
  </portType>
  <binding name="StreamingBinding" type="tns:StreamingPort">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    ${bindOps.join('\n    ')}
  </binding>
  <service name="StreamingService">
    <port name="StreamingPort" binding="tns:StreamingBinding">
      <soap:address location="${location}"/>
    </port>
  </service>
</definitions>`;
}

module.exports = { buildWsdl, OPS, TNS };
