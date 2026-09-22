'use strict';
const assert = require('node:assert/strict');
const data = require('../data/okinawan/mappings.json');
const {createInput} = require('../site/okinawan.js');
const input = createInput(data);
const convert = (s, system='funatsu', method='romaji') => input.convert(s, system, method).text;
const output = id => input.text(data.characters.find(e => e.id === id));
for (const e of data.characters) {
  assert.equal(convert(`{${e.id}}`, e.system, 'kana'), input.text(e), e.id);
  assert.equal(convert(`{${e.id}}`, e.system, 'romaji'), input.text(e), e.id);
  assert.equal(convert(e.id, e.system), input.text(e), e.id);
  if (e.kana) assert.equal(convert(e.kana, e.system, 'kana'), input.text(e), e.id);
  for (const alias of e.legacy || []) assert.equal(input.normalize(String.fromCodePoint(parseInt(alias,16))), input.text(e));
}
for (const [source,result] of [
  ['tui utu', output('tu')+'い う'+output('tu')],
  ['shi si chi ti tsu tu','し '+output('si')+' ち '+output('ti')+' つ '+output('tu')],
  ['du di gwa gwi gwe zi dzi', ['du','di','gwa','gwi','gwe','zi','dzi'].map(output).join(' ')],
  ["'ya ya 'n n", output("'ya")+' や '+output("'n")+' ん'],
  ["kan'i", 'かんい'],['nna','んな'],['nn','ん'],['onna','おんな'],
  ['kitta','きった'],['xtsu ltsu','っ っ'],['a-i','あーい'],
  ['yi ye','い\u3099 え\u3099'],['🌺 日本語 ABC','🌺 日本語 ABC'],
]) assert.equal(convert(source),result,source);
assert.equal(convert('utu ^uutu','prefecture'),'ウトゥ '+output('^u')+'ウトゥ');
assert.equal(convert('tsa tse tso nye wo dzi tya dyu cha', 'prefecture'), 'ツァ ツェ ツォ ニェ ウォ ズィ テャ デュ チャ');
assert.equal(convert('ti tu si tsi','prefecture'),'ティ トゥ スィ ツィ');
assert.equal(convert('^tsuヤ ^fuァ ^nマ','prefecture','kana'),output('^tsu')+'ヤ '+output('^fu')+'ァ '+output('^n')+'マ');
assert.equal(convert('English とぅ か\u3099 🌺','funatsu','kana'),'English '+output('tu')+' が 🌺');
assert.equal(convert('{tu}', 'prefecture', 'kana'),'{tu}');
assert.equal(input.convert('{tu}', 'prefecture').warnings.length,1);
assert.equal(input.convert('qzx', 'funatsu','romaji').warnings.length,3);
assert.equal(convert('\uFA80','funatsu','kana'),'\uFA80');
assert.equal(convert('\u{1B168}','funatsu','kana'),'\u{1B168}');
assert.equal(input.normalize(input.normalize('\uF451い\u3099')),input.normalize('\uF451い\u3099'));
assert.throws(() => input.convert('a', 'missing'));
assert.throws(() => input.convert('a', 'funatsu','missing'));
console.log('Okinawan input: 35 forms, Unicode storage, legacy PUA, nasal boundaries, gemination, mixed text and both systems passed.');
