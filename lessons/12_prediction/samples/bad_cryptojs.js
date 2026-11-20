// 转录自 CryptoJS 3.x 的 WordArray.random —— Ill Bloom（CVE-2026-71851）
// 熵从 2^128 掉到约 2^39。这不是 AI 写的，是 2014 年的人写的。
function badRandom(nBytes) {
  var words = [];
  for (var i = 0, rcache; i < nBytes; i += 4) {
    var seed = (rcache || Math.random()) * 0x100000000;
    rcache = mwc(seed) * 0x3ade67b7;
    words.push((mwc(seed) * 0x100000000) | 0);
  }
  return words;
}
