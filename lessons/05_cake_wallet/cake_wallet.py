#!/usr/bin/env python3
"""
第 5 课 · Cake Wallet —— 不安全的那个是默认值。

    python3 cake_wallet.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section, fmt_dt                      # noqa: E402
from bip39 import entropy_to_mnemonic                           # noqa: E402

MASK64 = (1 << 64) - 1
MASK32 = 0xFFFFFFFF
_A = 0xFFFFDA61            # Dart dart:math Random 的乘数


class DartRandom:
    """
    Dart 的 `Random()`（非 secure 的那个）。这是个 LCG 变体，文档里就写着
    「不适合密码学用途」。Dart VM 的 _nextState：

        state = (_A * (state & 0xFFFFFFFF)) + (state >> 32)

    Random() 不带 seed 的时候由 VM 播种，Milk Sad 测到的有效熵是 **20 位**
    （来源是微秒级时间，但实际可变范围远小于微秒的理论空间）。
    """

    def __init__(self, seed):
        # Dart 对种子做一次混合，确保高低 32 位都非零
        self._state = 0
        s = seed
        while True:
            low = s & MASK32
            s = (s - low) >> 32
            mix = ((_A * (self._state & MASK32)) + (self._state >> 32)) & MASK64
            self._state = (mix ^ low) & MASK64
            if s in (0, -1):
                break

    def _next(self):
        self._state = ((_A * (self._state & MASK32)) + (self._state >> 32)) & MASK64
        return (self._state >> 32) & MASK32

    def next_int(self, bound):
        return self._next() % bound


# ──────────────────────────────────────────────────────────────────────
# 这就是那个 bug，一字不多。
# ──────────────────────────────────────────────────────────────────────

def random_bytes(length, secure=False):            # ← 默认 False
    """Cake Wallet 自己包的那一层。注意默认参数。"""
    if secure:
        return os.urandom(length)                  # 对的那条路
    rng = DartRandom(int(time.time() * 1e6))        # 错的那条路
    return bytes(rng.next_int(256) for _ in range(length))


def generate_mnemonic_BUGGY():
    """原版：忘了传 secure: true。"""
    return entropy_to_mnemonic(random_bytes(32))


def generate_mnemonic_FIXED():
    """修复：加 14 个字符。"""
    return entropy_to_mnemonic(random_bytes(32, secure=True))


def weak_bytes_from_seed(seed, length=32):
    rng = DartRandom(seed)
    return bytes(rng.next_int(256) for _ in range(length))


def main():
    banner(5, "Cake Wallet（2020–2021）",
           "自己包了一层 randomBytes(length, {secure = false})，"
           "而生成助记词的那个调用忘了传 secure: true。不安全的那个是默认值。",
           "Milk Sad 研究更新 #6/#9/#10。厂商 2021-05 自披露。有效熵 20 位。")

    section("1 · 整个 bug 就是一个默认参数")
    print("""  Dart 原代码的形状：

      Uint8List randomBytes(int length, {bool secure = false}) { ... }
                                              ^^^^^^^^^^^^^^
      String generateMnemonic() => bip39.entropyToMnemonic(randomBytes(32));
                                                                      ^^^^
                                                           少传了一个命名参数

  **修复是 14 个字符。**代价是 8,757 个钱包、548.9 BTC 的流量。

  这一课要你记住的不是 Dart，是那个 API 的形状：
  **一个安全相关的开关，默认值是不安全的那一侧。** 任何这样的 API 都迟早会被漏掉。""")

    section("2 · 两条路，看一眼区别")
    print(f"  BUGGY: {' '.join(generate_mnemonic_BUGGY().split()[:6])} ...")
    print(f"  BUGGY: {' '.join(generate_mnemonic_BUGGY().split()[:6])} ...")
    print(f"  FIXED: {' '.join(generate_mnemonic_FIXED().split()[:6])} ...")
    print("\n  **看不出任何区别。** 词数对、校验位对、导进任何钱包都正常收发。")
    print("  第 1 道门的失败是静默的 —— 这就是那句话的字面含义。")

    section("3 · 把 20 位的空间整个走完")
    BITS = 20
    n = 1 << BITS
    victim_seed = 0x51234 & (n - 1)        # 固定 demo 种子
    victim = weak_bytes_from_seed(victim_seed)
    print(f"  demo 受害者（虚构，固定种子 {victim_seed}）")
    print(f"  助记词: {' '.join(entropy_to_mnemonic(victim).split()[:5])} ...")
    print(f"\n  穷举 2^{BITS} = {n:,} 个种子。先比 4 个字节，命中了再比全量。")
    prefix = victim[:4]
    t0 = time.perf_counter()
    found, tried = None, 0
    for s in range(n):
        tried += 1
        if weak_bytes_from_seed(s, 4) == prefix:
            if weak_bytes_from_seed(s, 32) == victim:
                found = s
                break
    dt = time.perf_counter() - t0
    print(f"\n  ✅ 种子 = {found}，{tried:,} 次尝试，{dt:.1f} 秒，{tried / dt:,.0f} 候选/秒")
    print(f"  完整助记词: {entropy_to_mnemonic(weak_bytes_from_seed(found))}")
    print(f"\n  **整个空间**（不是运气好，是 2^20 本来就这么大）本机要 {fmt_dt(n / (tried / dt))}。")
    print("  这是本课程里唯一一个能在一台笔记本上**从头走到尾**的真实案例空间。")

    section("4 · 本课程最重要的一条校准：披露之后发生了什么")
    print("""  Cake Wallet 是唯一一个有完整「披露之后」纵向记录的案例。

      2021-05      厂商自己发现，大张旗鼓披露，发补丁，要求用户紧急转移资金
                   （Reddit 一公开，几小时内就有网友读代码指出了确切技术原因）
      2021 年中    峰值 88 BTC 以上躺在弱钱包里
      2023 年底    研究者在**披露 2.5 年后**还发现有余额
      2024-05-21   大额恶意转出主要从这天才开始 —— 距公开披露三年

  **这条校准两头都砍：**

    往乐观的方向 —— 弱钥匙不会被瞬间扫光，存在一个真实的、以年计的反应窗口。
    往悲观的方向 —— 清扫最终一定会来，而且来的时候是**完整且同时**的。
                    三年没动的人，在某一天一次性全部失去。

  为什么会有这个窗口？不是运气。见第 13 课 Coinspect 那个攻防不对称。""")

    section("5 · 数字")
    print("""      8,757 个    唯一的弱主钱包（下界）
      548.9 BTC   2020-11-30 → 2024-10-10 间流经这些钱包的量
      20 位       有效熵
      14 个字符   修复的大小""")


if __name__ == "__main__":
    main()
