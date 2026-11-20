# 转录自 Cake Wallet 的 randomBytes —— 不安全的那个是默认值。
# 修复是 14 个字符。代价是 8,757 个钱包。
import os
import random
import time


def random_bytes(length, secure=False):
    if secure:
        return os.urandom(length)
    rng = random.Random(int(time.time() * 1e6))
    return bytes(rng.randint(0, 255) for _ in range(length))


def generate_mnemonic():
    return entropy_to_mnemonic(random_bytes(32))      # 忘了传 secure=True
