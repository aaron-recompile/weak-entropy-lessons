# 正确的样子：直接用操作系统的密码学随机源，没有包装层，没有 fallback，
# 失败就让它抛出来。
import os

from bip39 import entropy_to_mnemonic


def generate_mnemonic(strength_bits=256):
    assert strength_bits in (128, 256)
    entropy = os.urandom(strength_bits // 8)      # 失败会抛 OSError —— 这是对的
    return entropy_to_mnemonic(entropy)
