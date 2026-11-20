// CryptoJS 3.x 里那个坏掉的 WordArray.random，原封不动抄过来。
// 出处：crypto-js 3.1.2 ~ 3.3.0 的 core.js。4.0.0 已修。CVE-2026-71851 / Ill Bloom。
// 这里把 Math.random 做成可注入的，为了能复现「第一个钱包」。
'use strict';

function makeRandom(mathRandom) {
  return function random(nBytes) {
    var words = [];

    var r = (function (m_w) {
      var m_w = m_w;
      var m_z = 0x3ade68b1;              // ← 硬编码常量，不是熵
      var mask = 0xffffffff;

      return function () {
        m_z = (0x9069 * (m_z & 0xFFFF) + (m_z >> 0x10)) & mask;
        m_w = (0x4650 * (m_w & 0xFFFF) + (m_w >> 0x10)) & mask;
        var result = ((m_z << 0x10) + m_w) & mask;
        result /= 0x100000000;
        result += 0.5;
        return result * (mathRandom() > 0.5 ? 1 : -1);
      };
    });

    for (var i = 0, rcache; i < nBytes; i += 4) {
      var _r = r((rcache || mathRandom()) * 0x100000000);
      rcache = _r() * 0x3ade67b7;
      words.push((_r() * 0x100000000) | 0);
    }
    return words;                        // 32 位有符号字，每 4 字节一个
  };
}

function wordsToBytes(words, nBytes) {
  var out = Buffer.alloc(nBytes);
  for (var i = 0; i < nBytes; i++) {
    out[i] = (words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff;
  }
  return out;
}

if (require.main === module) {
  var mode = process.argv[2] || 'zero';
  var nBytes = parseInt(process.argv[3] || '16', 10);
  var mr;
  if (mode === 'zero') mr = function () { return 0; };
  else if (mode === 'real') mr = Math.random;
  else { var v = parseFloat(mode); mr = function () { return v; }; }
  var words = makeRandom(mr)(nBytes);
  console.log(JSON.stringify({ words: words, hex: wordsToBytes(words, nBytes).toString('hex') }));
}
module.exports = { makeRandom: makeRandom, wordsToBytes: wordsToBytes };
