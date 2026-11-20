// 正确的样子（浏览器）：没有 try/catch，没有 ||，没有 fallback。
// crypto.getRandomValues 不可用就让它炸 —— 随机数失败必须是致命错误。
function generateEntropy(nBytes) {
  const buf = new Uint8Array(nBytes);
  crypto.getRandomValues(buf);
  return buf;
}
