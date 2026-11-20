// 应用 B：依赖里有**同一个**有缺陷的库，但只用来做界面上的占位 id。
// 钱包生成走的是系统 CSPRNG。这个**不受影响** —— 但依赖扫描会把它和 A 一起报出来。
const CryptoJS = require('crypto-js');

function placeholderId() {
  // ← 同一个缺陷函数，但它的输出只进了一个 DOM id，不碰任何密钥
  return 'row-' + CryptoJS.lib.WordArray.random(4).toString();
}

function createWallet() {
  const entropy = new Uint8Array(16);
  crypto.getRandomValues(entropy);          // ← 真正生成钱包的是这一行
  return entropyToMnemonic(entropy);
}
module.exports = { createWallet, placeholderId };
