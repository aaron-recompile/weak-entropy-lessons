// 转录自 Randstorm 的形状：JSBN 的 SecureRandom 在当年的浏览器里退回 Math.random()。
// 本课证据分级里 Randstorm 是最弱的一条（见 README），但这个**形状**是硬的：
// 「在 CSPRNG 外面套一层 fallback」。
function getRandomBytes(n) {
  try {
    var buf = new Uint8Array(n);
    window.crypto.getRandomValues(buf);
    return buf;
  } catch (e) {
    // 老浏览器没有 crypto —— 退回去
    var out = [];
    for (var i = 0; i < n; i++) out.push(Math.floor(Math.random() * 256));
    return out;
  }
}
