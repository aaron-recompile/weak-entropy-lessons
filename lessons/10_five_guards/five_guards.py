#!/usr/bin/env python3
"""
第 10 课 · 五道保险，五道都没响 —— 因为五道都在检查输出。

    python3 five_guards.py
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
from lesson import banner, section                              # noqa: E402

M32 = 0xFFFFFFFF


class SoftwarePRNG:
    """
    一个「正常推进的软件 PRNG」—— 就是那个被绑错的东西。
    注意它有一个计数器，用来在最后演示「检查路径」的那个自检。
    """

    def __init__(self, seed):
        self.pad, self.n, self.d, self.dat = seed & M32, 0, 0, 0
        self.calls = 0
        self.hw_reads = 0            # ← 真的从硬件寄存器读了几次。一直是 0。

    def next_word(self):
        self.calls += 1
        self.pad = (self.pad + self.dat + self.d * self.n) & M32
        self.pad = ((self.pad << 3) | (self.pad >> 29)) & M32
        self.n = self.pad | 2
        self.d = (self.d ^ ((self.pad << 31) + (self.pad >> 1))) & M32
        self.dat = (self.dat ^ (self.pad & 0xFF) ^ ((self.d >> 8) & 0xFF) ^ 1) & 0xFF
        return (self.pad ^ ((self.d << 5) & M32) ^ (self.pad >> 18) ^ (self.dat << 1)) & M32

    def bytes(self, n):
        out = bytearray()
        while len(out) < n:
            out += self.next_word().to_bytes(4, "little")
        return bytes(out[:n])


# ── 五道保险，每一道都原样写成一个函数 ────────────────────────────────

def guard2_consecutive(words):
    """保险之二（运行期）：if (chip == last) fail hard. 「也许 TRNG 没上时钟？」"""
    for a, b in zip(words, words[1:]):
        if a == b:
            return False, "前后两个字相同"
    return True, "前后两个字从不相同"


def guard3_diversity(seed32: bytes):
    """保险之三：assert len(set(seed)) > 4 —— 32 字节里至少 5 个不同的值。"""
    d = len(set(seed32))
    return d > 4, f"32 字节里有 {d} 个不同的值（要求 > 4）"


def guard5_statistics(data: bytes):
    """
    保险之五：统计检验（真实固件里跑的是 Dieharder）。
    这里实现四个标准检验，自己算，不依赖外部工具。
    """
    bits = "".join(format(b, "08b") for b in data)
    n = len(bits)
    results = []

    # ① 单比特频率检验（monobit）
    ones = bits.count("1")
    z = abs(ones - n / 2) / math.sqrt(n / 4)
    results.append(("单比特频率 (monobit)", f"z = {z:.3f}", z < 2.576))

    # ② 字节分布卡方检验（256 个桶）
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    exp = len(data) / 256
    chi2 = sum((c - exp) ** 2 / exp for c in counts)
    # df=255，0.1%/99.9% 的临界值约 [185, 330]
    results.append(("字节分布卡方 (df=255)", f"χ² = {chi2:.1f}", 185 < chi2 < 330))

    # ③ 游程检验（runs test）
    runs = 1 + sum(1 for i in range(1, n) if bits[i] != bits[i - 1])
    p = ones / n
    exp_runs = 2 * n * p * (1 - p) + 1
    sd = math.sqrt(2 * n * p * (1 - p) * (2 * n * p * (1 - p) - 1) / (n - 1))
    zr = abs(runs - exp_runs) / sd
    results.append(("游程检验 (runs)", f"z = {zr:.3f}", zr < 2.576))

    # ④ 序列相关系数
    xs = list(data)
    m = sum(xs) / len(xs)
    num = sum((xs[i] - m) * (xs[i + 1] - m) for i in range(len(xs) - 1))
    den = sum((x - m) ** 2 for x in xs)
    corr = num / den if den else 0
    results.append(("序列相关系数", f"r = {corr:+.5f}", abs(corr) < 0.01))
    return results


def path_check(rng, want_words):
    """
    **唯一一个正确形状的检查** —— Coldcard 2026-08 的 commit 099b72f5：
    开机自检，数一下 rng_get() 到底从**硬件读取路径**上拉了几个字，
    数不对就把设备变砖。

    Wizardsardine 的评价：这是整个故事里唯一一个检查「路径」而不是检查「输出」的检查。
    """
    before = rng.hw_reads
    for _ in range(want_words):
        rng.next_word()
    got = rng.hw_reads - before
    return got == want_words, f"期望从硬件路径读 {want_words} 个字，实际读到 {got} 个"


def main():
    banner(10, "五道保险，五道都没响",
           "Coldcard 装了五道保险去防这件事，五道全部以不同方式失效。"
           "共同点：**它们全都在检查输出，没有一条在检查来源。**",
           "Wizardsardine 逐 commit 解剖 2026-08-11，第 7–13 节。")

    rng = SoftwarePRNG(0x0041002A ^ 1234)       # 和第 7 课同一个 demo 种子
    words = [rng.next_word() for _ in range(4096)]
    seed32 = SoftwarePRNG(0x0041002A ^ 1234).bytes(32)
    data = SoftwarePRNG(0x0041002A ^ 1234).bytes(125_000)   # 1 Mbit，给统计检验

    print(f"  被测对象：那个被绑错的软件 PRNG，种子 0x{0x0041002A ^ 1234:08X}")
    print(f"  它的输出完全确定 —— 同一台设备每次开机都一样。")
    print(f"  现在让五道保险逐一检查它。\n")

    section("保险 ① 构建期守卫 `#ifndef MICROPY_HW_ENABLE_RNG → #error`")
    print("  它测的是这个宏**有没有被定义**，而不是它的**值**。")
    print("  STM32 的 mpconfigboard_common.h **总是**定义它，默认 0。\n")
    cc = os.environ.get("CC", "cc")
    src = os.path.join(HERE, "guard1_macro.c")
    out = os.path.join(HERE, "build_guard1")
    os.makedirs(out, exist_ok=True)
    for flag, label in ((1, "真实固件的写法 #ifndef"), (0, "正确的写法 #if !VALUE")):
        r = subprocess.run([cc, f"-DGUARD_STYLE_IFNDEF={flag}", src, "-o",
                            os.path.join(out, f"g{flag}")],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  {label:<26} → 编译通过 ❌（守卫没响，构建继续）")
            for line in subprocess.run([os.path.join(out, f"g{flag}")],
                                       capture_output=True, text=True).stdout.splitlines():
                print("    " + line.strip())
        else:
            err = [l for l in r.stderr.splitlines() if "error" in l]
            print(f"  {label:<26} → 构建中止 ✅")
            print(f"      {err[0].strip() if err else r.stderr.splitlines()[0]}")
    print("\n  → **这道守卫在这个平台上永远不可能触发。** 它从来没有机会响。")

    section("保险 ② 运行期 `if (chip == last) fail hard`（「也许 TRNG 没上时钟？」）")
    ok, why = guard2_consecutive(words)
    print(f"  检查 {len(words):,} 个连续输出字：{why}")
    print(f"  结果：{'通过 ❌（保险没响）' if ok else '触发 ✅'}")
    print("""
  → 它只比较**前后两个输出字**。一个正常推进的软件 PRNG 轻松通过。
    它能抓的只是「外设永远返回同一个值」这一种故障 —— 而这不是发生的那种故障。""")

    section("保险 ③ `assert len(set(seed)) > 4`")
    ok, why = guard3_diversity(seed32)
    print(f"  弱 PRNG 的 32 字节种子：{why} → {'通过 ❌' if ok else '触发 ✅'}")
    ok2, why2 = guard3_diversity(os.urandom(32))
    print(f"  真随机的 32 字节种子  ：{why2} → {'通过' if ok2 else '触发'}")
    # 均匀随机下掉到 <=4 个不同值的概率
    print("""
  → 这测的是**多样性**，不是**可预测性**。
    均匀随机下大约有 30 个不同值；掉到 ≤4 的概率约 2^-165。
    **这个断言永远不会响** —— 它的触发条件比弱熵本身还罕见得多。""")

    section("保险 ④ MicroPython 的 `#if MICROPY_HW_ENABLE_RNG`")
    print("""  这一道最微妙，因为它看起来是对的：

      uint32_t rng_get(void) {
      #if MICROPY_HW_ENABLE_RNG
          ... 读硬件寄存器 ...        ← 守卫守着这一侧
      #else
          return yasmarang();        ← 出问题的是这一侧，没有任何守卫
      #endif
      }

  → **它守的是硬件那一侧的实现，不是软件 fallback 那一侧。**
    守卫装在了没有危险的那条分支上。""")

    section("保险 ⑤ 统计检验（真实固件里跑的是 Dieharder）")
    print(f"  对那个弱 PRNG 的 {len(data) * 8:,} 比特输出跑四个标准检验：\n")
    for name, stat, passed in guard5_statistics(data):
        print(f"    {name:<24} {stat:<18} {'通过 ❌' if passed else '不通过 ✅'}")
    print("\n  对照组，真随机：\n")
    for name, stat, passed in guard5_statistics(os.urandom(125_000)):
        print(f"    {name:<24} {stat:<18} {'通过' if passed else '不通过'}")
    print("""
  → **全部通过。** 而被测的那个东西，每次开机输出完全一样。

    这不是检验写得不好 —— 这是统计检验的本质：
    **它检查「这些字节看起来随机吗」，而弱熵的字节看起来确实随机。**
    坏的不是分布，坏的是「这条流一共只有 400 万条」这件事，
    而这件事在任何单条流的样本里都看不见。

    真实固件里那个检验（testing/test_rng.py，2021-03-16 加入，
    **比 bug 进代码只晚了 15 天**）还多栽了一跤：不加 --dev 时它在
    **桌面模拟器**上取数，而模拟器里 CHIP_TRNG_32() 接的是**主机 libc**
    —— 被测的字节从来不来自那个出问题的路径。""")

    section("五条的共同点 —— 本课要你记住的唯一一句")
    print("""      ① 检查宏有没有被定义      —— 检查构建配置的形状
      ② 检查前后两个字是否相同  —— 检查输出
      ③ 检查 32 字节里几个不同  —— 检查输出
      ④ 检查硬件那一侧的实现    —— 守在了没危险的分支上
      ⑤ 跑 Dieharder            —— 检查输出

  **没有一条在问：这些字节是从哪来的？**""")

    section("那个正确形状的检查长什么样")
    print("""  2026-08 的 commit 099b72f5 加了一个开机自检：
  **数一下 rng_get() 到底从硬件读取路径上拉了几个字，数不对就把设备变砖。**

  Wizardsardine 的评价：这是**整个故事里唯一一个检查「路径」而不是检查「输出」**的检查。
  现在用它检查同一个弱 PRNG：
""")
    rng2 = SoftwarePRNG(0x0041002A ^ 1234)
    ok, why = path_check(rng2, 32)
    print(f"    {why}")
    print(f"    结果：{'通过' if ok else '**触发 ✅ —— 第一个真正抓住它的检查**'}")
    print("""
  它为什么能抓住：因为它问的问题，**只有正确的实现才答得对**。
  一个软件 PRNG 无论输出多漂亮，都没法假装自己读过那个寄存器。

  ⚠️  截至 Wizardsardine 2026-08-11 那篇发表时，**这两个自检都还没发版**
      （Mk3 侧归到 4.2.1，仍标 TBD）。这是信号表该盯的一条，而且可核。

  → **如果你要设计一个自己的熵验证实验，设计成验证路径，而不是验证分布。**
    这是整份研究里最有用的一条方法。
    （而第 7 课那个 15 行的 verify_symbols.sh 就是一个验证路径的例子。）""")


if __name__ == "__main__":
    main()
