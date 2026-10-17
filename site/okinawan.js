/* Shared by the offline page and Node input tests. No external input service. */
(function (root) {
  'use strict';
  function createInput(data) {
    const entries = data.characters;
    const text = entry => String.fromCodePoint(...entry.output.map(cp => parseInt(cp, 16)));
    const legacy = new Map(entries.flatMap(e => (e.legacy || []).map(cp => [String.fromCodePoint(parseInt(cp, 16)), text(e)])));
    const normalize = value => [...value].map(ch => legacy.get(ch) || ch).join('').replace(/[\u3041-\u3096\u30A1-\u30FA][\u3099\u309A]+/gu, kana => kana.normalize('NFC'));
    const ordinary = {};
    const rows = {
      '': 'あいうえお', k: 'かきくけこ', g: 'がぎぐげご', s: 'さしすせそ', z: 'ざじずぜぞ',
      t: 'たちつてと', d: 'だぢづでど', n: 'なにぬねの', h: 'はひふへほ', b: 'ばびぶべぼ',
      p: 'ぱぴぷぺぽ', m: 'まみむめも', r: 'らりるれろ',
    };
    for (const [consonant, kana] of Object.entries(rows)) {
      [...kana].forEach((ch, i) => { ordinary[consonant + 'aiueo'[i]] = ch; });
    }
    Object.assign(ordinary, {ya:'や',yu:'ゆ',yo:'よ',wa:'わ',wi:'ゐ',we:'ゑ',wo:'を',
      shi:'し',chi:'ち',tsu:'つ',fu:'ふ',ji:'じ',ja:'じゃ',ju:'じゅ',jo:'じょ',
      she:'しぇ',che:'ちぇ',je:'じぇ',fa:'ふぁ',fi:'ふぃ',fe:'ふぇ',fo:'ふぉ',
      kwa:'くゎ',kwi:'くぃ',kwe:'くぇ',gwa:'ぐゎ',gwi:'ぐぃ',gwe:'ぐぇ',
      hwa:'ふゎ',hwi:'ふぃ',hwe:'ふぇ',wu:'をぅ',yi:'い\u3099',ye:'え\u3099',tsi:'つぃ',dzi:'づぃ'});
    for (const [prefix, first] of Object.entries({ky:'き',gy:'ぎ',sh:'し',ch:'ち',ny:'に',hy:'ひ',by:'び',py:'ぴ',my:'み',ry:'り',sy:'し',zy:'じ',ty:'ち',dy:'ぢ',jy:'じ'})) {
      for (const [vowel, small] of Object.entries({a:'ゃ',u:'ゅ',o:'ょ'})) ordinary[prefix+vowel] = first+small;
    }
    for (const prefix of ['x', 'l']) {
      for (const [key, ch] of Object.entries({a:'ぁ',i:'ぃ',u:'ぅ',e:'ぇ',o:'ぉ',ya:'ゃ',yu:'ゅ',yo:'ょ',wa:'ゎ',tsu:'っ',tu:'っ'})) ordinary[prefix+key] = ch;
    }
    const katakana = s => [...s].map(ch => {
      const cp = ch.codePointAt(0);
      return cp >= 0x3041 && cp <= 0x3096 ? String.fromCodePoint(cp+0x60) : ch;
    }).join('');

    function convert(source, system = 'funatsu', method = 'kana') {
      if (!['funatsu', 'prefecture'].includes(system) || !['kana', 'romaji'].includes(method)) throw new Error('Unknown input mode');
      const active = entries.filter(e => e.system === system);
      const tokens = new Map(active.map(e => [e.id, text(e)]));
      const roman = {...ordinary};
      if (system === 'funatsu') active.forEach(e => { roman[e.id] = text(e); });
      else {
        Object.assign(roman, {tsa:'つぁ',tse:'つぇ',tso:'つぉ',nye:'にぇ',wo:'うぉ',tya:'てゃ',tyu:'てゅ',tyo:'てょ',dya:'でゃ',dyu:'でゅ',dyo:'でょ',dzi:'ずぃ',tu:'とぅ',ti:'てぃ',du:'どぅ',di:'でぃ',si:'すぃ',zi:'ずぃ',wu:'う',yi:'い',ye:'いぇ',wi:'うぃ',we:'うぇ'});
        Object.keys(roman).forEach(key => { roman[key] = katakana(roman[key]); });
      }
      const kana = active.filter(e => e.kana).sort((a,b) => b.kana.length-a.kana.length);
      const keys = Object.keys(roman).sort((a,b) => b.length-a.length);
      let input = normalize(source), output = '', warnings = [];
      for (let i = 0; i < input.length;) {
        const rest = input.slice(i);
        // Explicit braces are available in both input modes; unknown commands
        // remain intact so changing systems cannot silently reinterpret them.
        const command = rest.match(/^\{([^{}]*)\}/u);
        if (command) {
          const value = tokens.get(command[1]);
          output += value === undefined ? command[0] : value;
          if (value === undefined) warnings.push(`Unknown shortcut ${command[0]} for this system.`);
          i += command[0].length; continue;
        }
        if (system === 'prefecture') {
          const raised = rest.match(/^\^(tsu|fu|[aiueon])/);
          if (raised) { output += tokens.get(raised[0]); i += raised[0].length; continue; }
        }
        if (method === 'kana') {
          const match = kana.find(e => rest.startsWith(e.kana));
          if (match) { output += text(match); i += match.kana.length; continue; }
        } else {
          // n' is the syllabic nasal before a vowel; initial 'n is Funatsu's
          // glottal nasal. Explicit {'n} always resolves the latter.
          if (rest.startsWith("n'")) { output += system === 'funatsu' ? 'ん' : 'ン'; i += 2; continue; }
          if (/^n(?:$|[^aeiouy])/u.test(rest)) {
            output += system === 'funatsu' ? 'ん' : 'ン';
            i += rest === 'nn' || /^nn(?=[^aeiouy])/u.test(rest) ? 2 : 1; continue;
          }
          if (/^([bcdfghjkpqrstvwxyz])\1/u.test(rest) && keys.some(k => rest.slice(1).startsWith(k))) {
            output += system === 'funatsu' ? 'っ' : 'ッ'; i++; continue;
          }
          const key = keys.find(k => rest.startsWith(k));
          if (key) { output += roman[key]; i += key.length; continue; }
          if (rest[0] === '-') { output += 'ー'; i++; continue; }
          if (/[a-z]/.test(rest[0])) warnings.push(`Unconverted romaji: ${rest[0]}`);
        }
        const ch = String.fromCodePoint(input.codePointAt(i));
        output += ch; i += ch.length;
      }
      return {text: normalize(output), warnings: [...new Set(warnings)]};
    }
    return {convert, normalize, text, entries};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {createInput};
  else root.OkinawanInput = {createInput};
})(typeof globalThis !== 'undefined' ? globalThis : this);
