"""
BIP39：把一串字节变成助记词。纯标准库，没有依赖。

要点（第 10 课会用到）：这一步是**完全可逆的编码**，不是加密，不增加任何熵。
32 字节熵 → 24 个词。弱的 32 字节，变成弱的 24 个词，一个字节的秘密都没多出来。
"""
import hashlib
import hmac
import os
import unicodedata

_WORDLIST_PATH = os.path.join(os.path.dirname(__file__), "wordlist", "english.txt")
# BIP39 官方英文词表的 sha256，防止被换掉
WORDLIST_SHA256 = "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"


def load_wordlist(path=_WORDLIST_PATH, verify=True):
    with open(path, "rb") as f:
        raw = f.read()
    if verify:
        got = hashlib.sha256(raw).hexdigest()
        if got != WORDLIST_SHA256:
            raise SystemExit(f"词表被改过！期望 {WORDLIST_SHA256}，实际 {got}")
    return raw.decode().split()


WORDS = load_wordlist()
INDEX = {w: i for i, w in enumerate(WORDS)}


def entropy_to_mnemonic(entropy: bytes) -> str:
    """BIP39 编码。entropy 长度必须是 16/20/24/28/32 字节。"""
    if len(entropy) not in (16, 20, 24, 28, 32):
        raise ValueError(f"熵长度 {len(entropy)} 字节不合法")
    cs_len = len(entropy) * 8 // 32                       # 校验位位数
    checksum = hashlib.sha256(entropy).digest()[0] >> (8 - cs_len)
    bits = int.from_bytes(entropy, "big") << cs_len | checksum
    total = len(entropy) * 8 + cs_len
    n_words = total // 11
    idx = [(bits >> (11 * (n_words - 1 - i))) & 0x7FF for i in range(n_words)]
    return " ".join(WORDS[i] for i in idx)


def mnemonic_to_entropy(mnemonic: str) -> bytes:
    ws = mnemonic.split()
    bits = 0
    for w in ws:
        bits = (bits << 11) | INDEX[w]
    total = len(ws) * 11
    cs_len = total // 33
    ent_len = (total - cs_len) // 8
    ent = (bits >> cs_len).to_bytes(ent_len, "big")
    if (bits & ((1 << cs_len) - 1)) != hashlib.sha256(ent).digest()[0] >> (8 - cs_len):
        raise ValueError("校验位不对")
    return ent


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """BIP39 的 2048 轮 PBKDF2-HMAC-SHA512。第 10 课专门拆这一步。"""
    m = unicodedata.normalize("NFKD", mnemonic).encode()
    salt = unicodedata.normalize("NFKD", "mnemonic" + passphrase).encode()
    return hashlib.pbkdf2_hmac("sha512", m, salt, 2048, 64)


# --- BIP32 主私钥（为了能把种子推到地址，第 2 课要用） ---

def seed_to_master_key(seed: bytes):
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    return I[:32], I[32:]      # (私钥, chain code)


if __name__ == "__main__":
    # BIP39 官方测试向量，自检
    assert entropy_to_mnemonic(bytes(16)) == \
        "abandon abandon abandon abandon abandon abandon " \
        "abandon abandon abandon abandon abandon about"
    assert entropy_to_mnemonic(bytes(32)).startswith("abandon abandon")
    assert entropy_to_mnemonic(bytes.fromhex("7f" * 16)).split()[0] == "legal"
    m = entropy_to_mnemonic(bytes.fromhex("00" * 16))
    assert mnemonic_to_entropy(m) == bytes(16)
    assert mnemonic_to_seed(
        "abandon abandon abandon abandon abandon abandon "
        "abandon abandon abandon abandon abandon about", "TREZOR").hex().startswith("c55257c360c07c72")
    print("BIP39 自检通过（含官方测试向量）")
