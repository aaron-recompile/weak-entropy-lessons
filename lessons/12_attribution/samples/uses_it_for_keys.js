// 应用 A：依赖里有那个有缺陷的库，**而且用它生成钱包**。这个是真受影响的。
const CryptoJS = require('crypto-js');
const bip39 = require('bip39');

function createWallet() {
  // ← 缺陷的随机数直接喂进了助记词生成
  const entropy = CryptoJS.lib.WordArray.random(16);
  return bip39.entropyToMnemonic(Buffer.from(entropy.toString(), 'hex'));
}
module.exports = { createWallet };
