#!/usr/bin/env python3
"""
第 5 课 · PHP 的 mt_rand() —— 同一段代码，三个不同的弱钱包范围。

    python3 php_mt_rand.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section                              # noqa: E402

N, M = 624, 397
HI = 0x80000000
LO = 0x7FFFFFFF
MATRIX_A = 0x9908B0DF


class PhpMt:
    """
    PHP 的 Mersenne Twister，两个模式。

    关键在 twist 那一行。PHP 的 C 源码里是两个宏：

      正确（MT_RAND_MT19937，PHP 7.1 起的默认）：
        #define twist(m,u,v)     (m ^ (mixBits(u,v)>>1) ^ ((uint32_t)(-(int32_t)(loBit(v))) & 0x9908b0dfU))
                                                                                     ^^^^
      PHP 自己的（MT_RAND_PHP，约 2006–2019 的默认）：
        #define twist_php(m,u,v) (m ^ (mixBits(u,v)>>1) ^ ((uint32_t)(-(int32_t)(loBit(u))) & 0x9908b0dfU))
                                                                                     ^^^^
    差一个字母。u 和 v。**十三年里，全世界 PHP 生成的随机数都走的是下面那条。**
    """

    def __init__(self, seed, mode="MT_RAND_MT19937"):
        self.mode = mode
        self.s = [0] * N
        self.s[0] = seed & 0xFFFFFFFF
        for i in range(1, N):
            p = self.s[i - 1]
            self.s[i] = (1812433253 * (p ^ (p >> 30)) + i) & 0xFFFFFFFF
        self.i = N
        self._reload()

    def _twist(self, m, u, v):
        mixed = (u & HI) | (v & LO)
        lobit = (u if self.mode == "MT_RAND_PHP" else v) & 1
        return m ^ (mixed >> 1) ^ (MATRIX_A if lobit else 0)

    def _reload(self):
        s = self.s
        for i in range(N):
            s[i] = self._twist(s[(i + M) % N], s[i], s[(i + 1) % N])
        self.i = 0

    def next_u32(self):
        if self.i >= N:
            self._reload()
        y = self.s[self.i]
        self.i += 1
        y ^= y >> 11
        y = (y ^ ((y << 7) & 0x9D2C5680)) & 0xFFFFFFFF
        y = (y ^ ((y << 15) & 0xEFC60000)) & 0xFFFFFFFF
        y ^= y >> 18
        return y

    def mt_rand(self):
        """PHP 的 mt_rand() 不带参数时返回 php_mt_rand() >> 1。"""
        return self.next_u32() >> 1


def phpcoinaddress_privkey(seed, mode):
    """
    PHPCoinAddress（2013，给网店在服务器上批量生成收款地址用）的形状：

        for ($i = 0; $i < 32; $i++)
            $key .= chr(mt_rand(0, 255));

    加上一个真实存在的细节 —— 第一个字节走的是 `$i ? 0xff : 0xfe`，
    所以第一字节只有两个取值。这把搜索空间推到 2^41 / 2^40 量级而不是 2^32。
    """
    rng = PhpMt(seed, mode)
    # PHP 的 mt_rand(0, 255) 做的是区间缩放
    out = bytearray()
    for i in range(32):
        r = rng.mt_rand()
        out.append((r % 256) if i else (0xFE))
    return bytes(out)


def main():
    banner(5, "PHPCoinAddress / PHP mt_rand()（2013–2018）",
           "同一段 PHP 代码，在不同版本的 PHP 引擎上生成**完全不同**的钥匙 —— "
           "因为 PHP 二十年里至少改了三次 mt_rand() 的底层行为。",
           "Milk Sad 研究更新 #17/#18。bitcointalk 用户 Abdussamad 2013-12-13 公开点名。")

    section("1 · 两个模式，同一个种子")
    for seed in (42, 1337, 7):
        a = PhpMt(seed, "MT_RAND_MT19937")
        b = PhpMt(seed, "MT_RAND_PHP")
        va = [a.mt_rand() for _ in range(624)]
        vb = [b.mt_rand() for _ in range(624)]
        diff = sum(1 for x, y in zip(va, vb) if x != y)
        print(f"  seed={seed}")
        print(f"    MT_RAND_MT19937 前 4 个: {va[:4]}")
        print(f"    MT_RAND_PHP     前 4 个: {vb[:4]}")
        print(f"    一整轮 624 个输出里，{diff} 个不同（{diff / 6.24:.0f}%）")
    print("""
  为什么是一半：那个 twist 只在 `lobit(u) != lobit(v)` 的位置上产生分叉，
  而这两个比特在播种出来的状态里基本独立 —— 所以约 50%。
  **一半的输出不同，就已经是两个完全不相交的弱钱包空间。**""")
    print("""
  ⚠️  证据说明：这段实现是按 PHP 的 C 宏（php_mt_reload 里的 twist / twist_php）
      写的，**本机没装 PHP，所以没有和真实引擎交叉验证过。**
      你装了 PHP 之后可以一行核对：

          php -r 'mt_srand(42, MT_RAND_PHP); echo mt_rand(),",",mt_rand();'

      机理（差一个 u/v）是有一手出处的；本实现与真实引擎逐值一致这件事，没有。""")

    section("2 · 这意味着什么：一段代码，三个弱钱包范围")
    print("""      ~2006 年前          旧的初始化算法，把播种有效压到 **31 位**
      约 2006–2019        MT_RAND_PHP（那个 u/v 写错的 twist）
      约 2016 至今        MT_RAND_MT19937（标准的）

  所以同一个网店，同一份 PHPCoinAddress，装在三台不同 PHP 版本的服务器上，
  会落进三个**互不相交**的弱空间。研究者要分别枚举三遍。

  这是弱熵研究为什么这么慢的一个具体原因：**不是一个空间，是一族空间。**
  （「2006 年前压到 31 位」这条是案例库里的转述，我没读到 PHP 的原始 commit。）""")

    section("3 · 私钥长什么样")
    for mode in ("MT_RAND_MT19937", "MT_RAND_PHP"):
        k = phpcoinaddress_privkey(1380000000, mode)
        print(f"  {mode:<16} {k.hex()}")
    print("\n  注意第一个字节都是 fe —— `$i ? 0xff : 0xfe` 那一行。")
    print("  这种「一眼能看出来的结构」就是研究者认出一族弱钱包的办法。")

    section("4 · 爆破 + 那个让搜索空间变大的细节")
    t0 = time.perf_counter()
    n = 2000
    for s in range(n):
        phpcoinaddress_privkey(s, "MT_RAND_PHP")
    rate = n / (time.perf_counter() - t0)
    print(f"  本机速率: {rate:,.0f} 候选/秒（PHP 的 MT 每次都要跑一次完整 reload，比 bx 慢）")
    print(f"  研究者实际搜的是 2^41 / 2^40 —— 本机要 {2 ** 41 / rate / 86400 / 365:,.0f} 年。")
    print("  这个案例是 GPU 和专用代码的领域，不是笔记本的。")

    section("5 · 这一课的教训和别的都不一样")
    print("""  前面几课的受害者都是个人用户。这一课的受害者是**基础设施**：

      PHPCoinAddress 是给网店在**服务器上批量生成收款地址**用的。
      每个来买东西的顾客拿到一个新地址，而那个地址的私钥是 mt_rand() 生成的。

  时间线最值得看：

      2013 年初    库发布
      2013-12-13   bitcointalk 用户 Abdussamad 公开点名：
                   「这个脚本生成的私钥不安全，你可以看到第 240 行用了 mt_rand」
      2014         原作者弃坑
      然后         **用量持续了好几年。2017 年又被公开讨论了一次。**
      2012-10 起   7,713.5 BTC 流经这些地址
                   盗转尖峰：2015 年初、2016 年末、2018 年初

  **「公开披露」对这个案例完全无效，因为用它的人根本不读 bitcointalk。**
  从发布到被公开点名只有几个月 —— 这是全部 11 个案例里最快的发现，
  而它一点用都没有。

  → 「已披露」和「已修复」是两件事。「已修复」和「用户的钱安全了」是第三件事。""")


if __name__ == "__main__":
    main()
