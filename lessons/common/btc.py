"""
最小比特币地址推导 —— 纯标准库，没有依赖。

为什么课程里要带这个：弱熵的攻击链是四步
    种子空间 → 私钥 → 公钥 → 地址
只有走到最后一步，攻击者才能在链上「比对有没有钱」。
第 13 课讲的那个「以年计的反应窗口」，原因就在最后一步比前三步贵。

这段代码只做演示用的推导，不做签名，不联网，不碰任何真实钱包。
"""
import hashlib
import hmac

# secp256k1
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


def _add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    (x1, y1), (x2, y2) = p, q
    if x1 == x2:
        if (y1 + y2) % P == 0:
            return None
        lam = 3 * x1 * x1 * pow(2 * y1, P - 2, P) % P
    else:
        lam = (y2 - y1) * pow(x2 - x1, P - 2, P) % P
    x3 = (lam * lam - x1 - x2) % P
    return (x3, (lam * (x1 - x3) - y1) % P)


def privkey_to_point(priv: int):
    """标量乘法 —— 爆破里最贵的那一步。一个点算一次，两种编码都能出。"""
    if not 0 < priv < N:
        raise ValueError("私钥不在 [1, N-1] 区间")
    r, add = None, (GX, GY)
    while priv:
        if priv & 1:
            r = _add(r, add)
        add = _add(add, add)
        priv >>= 1
    return r


def point_to_pubkey(pt, compressed=True) -> bytes:
    x, y = pt
    if compressed:
        return bytes([2 + (y & 1)]) + x.to_bytes(32, "big")
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def privkey_to_pubkey(priv: int, compressed=True) -> bytes:
    """标量乘法。double-and-add，够用。"""
    if not 0 < priv < N:
        raise ValueError("私钥不在 [1, N-1] 区间")
    r, add = None, (GX, GY)
    while priv:
        if priv & 1:
            r = _add(r, add)
        add = _add(add, add)
        priv >>= 1
    x, y = r
    if compressed:
        return bytes([2 + (y & 1)]) + x.to_bytes(32, "big")
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def hash160(b: bytes) -> bytes:
    return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()


_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58check(payload: bytes) -> str:
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(payload + chk, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = _B58[r] + s
    return "1" * len(payload + chk) * 0 + _B58[0] * (len(payload) - len(payload.lstrip(b"\x00"))) + s


def p2pkh(pubkey: bytes) -> str:
    """1... 开头的传统地址。"""
    return b58check(b"\x00" + hash160(pubkey))


_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values):
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            chk ^= gen[i] if (b >> i) & 1 else 0
    return chk


def p2wpkh(pubkey: bytes, hrp="bc") -> str:
    """bc1q... 开头的 segwit v0 地址。"""
    prog = hash160(pubkey)
    data = [0] + [int(b, 2) for b in
                  [format(int.from_bytes(prog, "big"), "0160b")[i:i + 5] for i in range(0, 160, 5)]]
    exp = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    pm = _bech32_polymod(exp + data + [0] * 6) ^ 1
    checksum = [(pm >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_BECH32[d] for d in data + checksum)


# --- BIP32 ---

def bip32_master(seed: bytes):
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    return int.from_bytes(I[:32], "big"), I[32:]


def bip32_ckd_priv(k: int, c: bytes, index: int):
    if index >= 0x80000000:                                   # hardened
        data = b"\x00" + k.to_bytes(32, "big") + index.to_bytes(4, "big")
    else:
        data = privkey_to_pubkey(k) + index.to_bytes(4, "big")
    I = hmac.new(c, data, hashlib.sha512).digest()
    return (int.from_bytes(I[:32], "big") + k) % N, I[32:]


def derive_path(seed: bytes, path: str):
    """path 形如 m/84'/0'/0'/0/0"""
    k, c = bip32_master(seed)
    for part in path.split("/")[1:]:
        hardened = part.endswith("'") or part.endswith("h")
        idx = int(part.rstrip("'h")) + (0x80000000 if hardened else 0)
        k, c = bip32_ckd_priv(k, c, idx)
    return k, c


def mnemonic_first_address(mnemonic: str, passphrase="", path="m/84'/0'/0'/0/0") -> str:
    from bip39 import mnemonic_to_seed
    k, _ = derive_path(mnemonic_to_seed(mnemonic, passphrase), path)
    return p2wpkh(privkey_to_pubkey(k))


if __name__ == "__main__":
    # BIP32 官方测试向量 1：seed 000102...0f
    k, c = bip32_master(bytes.fromhex("000102030405060708090a0b0c0d0e0f"))
    assert k.to_bytes(32, "big").hex() == \
        "e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35", k
    # BIP84 官方测试向量（助记词 abandon ×11 + about）
    m = "abandon " * 11 + "about"
    assert mnemonic_first_address(m.strip()) == "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu"
    # 已知的 P2PKH 向量：私钥 1
    assert p2pkh(privkey_to_pubkey(1)) == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    print("比特币推导自检通过（BIP32 向量 1 + BIP84 向量 + privkey=1）")
