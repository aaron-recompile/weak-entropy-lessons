#!/usr/bin/env python3
"""
第 8 课 · XOR 不生产随机性。

    python3 xor_entropy.py
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section, human                        # noqa: E402

M32 = 0xFFFFFFFF


def prng_a(seed, n=4):
    """xorshift32。种子空间由调用方限定。"""
    s = (seed & M32) or 1
    out = []
    for _ in range(n):
        s ^= (s << 13) & M32
        s ^= s >> 17
        s ^= (s << 5) & M32
        out.append(s)
    return tuple(out)


def prng_b(seed, n=4):
    """一个结构完全不同的 LCG。"""
    s = seed & M32
    out = []
    for _ in range(n):
        s = (1664525 * s + 1013904223) & M32
        out.append(s)
    return tuple(out)


def xor(t1, t2):
    return tuple(a ^ b for a, b in zip(t1, t2))


def main():
    banner(8, "XOR 不生产随机性",
           "把两个弱随机数 XOR 在一起，不会变强。能 XOR 出强随机的前提是"
           "**至少有一个操作数本来就是强的** —— 而 Coldcard 那次，两个都不是。",
           "信息论：H(A⊕B) ≤ H(A) + H(B)。Coldcard 的具体形态见 Wizardsardine 2026-08-11。")

    section("1 · 大白话")
    print("""  Coldcard 代码**打算**做的事情完全正确：

      种子 = 硬件真随机数  XOR  软件 PRNG

  这是标准加固做法：即使软件 PRNG 被预测，物理噪声还在，所以结果不可预测。
  **问题是链接错误让第一个操作数也变成了软件 PRNG。**

      本来：不可预测 XOR 可预测 = 不可预测   ✅
      实际：可预测   XOR 可预测 = 可预测     ❌

  XOR 是个搅拌器，不是个泵。它能把熵混匀，不能把熵变多。""")

    section("2 · 把它穷举出来，不用相信我")
    KA, KB = 10, 10                                 # 各 2^10 个种子
    A = {prng_a(s) for s in range(1 << KA)}
    B = {prng_b(s) for s in range(1 << KB)}
    print(f"  PRNG A：2^{KA} 个种子 → {len(A):,} 条不同的输出")
    print(f"  PRNG B：2^{KB} 个种子 → {len(B):,} 条不同的输出")

    print(f"\n  注意 A 只给出 {len(A):,} 条，不是 1,024 条 —— 这是个真实存在的小陷阱：")
    print("  **xorshift 不能用 0 播种**（0 是不动点），所以代码里那个 `or 1` 把")
    print("  种子 0 和种子 1 悄悄合并成了同一条流。禁止的种子值会静默吃掉熵。")

    print("\n  情形甲：两个 PRNG 各自独立播种（种子相互独立）")
    xs = {xor(prng_a(a), prng_b(b)) for a in range(1 << KA) for b in range(1 << KB)}
    print(f"    XOR 的输出空间 = {len(xs):,} 条")
    print(f"    上界 = |A| × |B| = {len(A):,} × {len(B):,} = {len(A) * len(B):,}")
    print(f"    达到上界了吗: {len(xs) == len(A) * len(B)}  ← 独立播种时 XOR 确实加分，"
          f"而且一位不差")

    print("\n  情形乙：**两个 PRNG 从同一个种子出发**（Coldcard 的实际形态）")
    xs2 = {xor(prng_a(s), prng_b(s)) for s in range(1 << KA)}
    print(f"    XOR 的输出空间 = {len(xs2):,} 条")
    print(f"    = 2^{KA} —— **和种子空间一样大。XOR 一位都没加。**")
    print("    （输出条数由那一个共同的种子数决定，两个 PRNG 的结构再不同也没用。）")

    print("\n  情形丙：一个强 + 一个弱（本该有的样子）")
    xs3 = {xor(tuple(int.from_bytes(os.urandom(4), 'big') for _ in range(4)), prng_b(s))
           for s in range(1 << KA)}
    print(f"    {1 << KA} 次抽样 → {len(xs3):,} 条不同，没有一次重复")
    print("    强的那个操作数把整个结果撑起来了。**这就是加固的本意。**")
    print("    （注意：抽样只能证明它不小，证不出它多大 —— 这正是第 10 课的主题。）")

    section("3 · 为什么 Coldcard 落在情形乙")
    print("""  链接期把 rng_get 绑到了软件 PRNG 上，所以：

      硬件操作数  ← 其实是 Yasmarang(UID ^ SysTick)
      软件操作数  ← 另一个软件 PRNG

  两个都是从同一台机器、同一次开机的那几个不保密的 32 位值算出来的。
  **它们不是独立的两个熵源，是同一个熵源的两个函数。**

  更糟的是第 7 课演示过的那一点：UID 和 SysTick 本身也是 XOR 进同一个
  32 位字里的，所以它们也会互相抵消 —— 不是 32+32 位，是最多 32 位。

  整条链上 XOR 出现了两次，两次都没有增加任何东西。""")

    section("4 · 一个反直觉的推论")
    print("""  **「我们混合了多个熵源」这句话，本身不构成任何保证。**

  要让混合有意义，必须能回答：**这些源里，哪一个是不可预测的？**
  如果答案是「都差不多」，那混合的结果就是其中最好的那一个，不是它们的和。

  这条推论可以直接拿来检查任何钱包的熵设计：
      ✅ 「系统 CSPRNG，直接用，不混」—— 不需要论证
      ✅ 「硬件 TRNG XOR 系统 CSPRNG」—— 两个都强，怎么混都对
      ⚠️  「混了时间、鼠标移动、进程 ID、设备序列号」—— 全部可观测，和 = 0
      ❌ 「混了两个 PRNG」—— 第 7 课就是这个

  第 10 课会让你看到：这件事**没有任何统计检验能发现**，
  因为 XOR 把分布搅得很漂亮。坏的是来源，不是分布。""")


if __name__ == "__main__":
    main()
