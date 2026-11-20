#!/usr/bin/env python3
"""
第 7 课 · 脑钱包 —— 不是 bug，是设计。弱熵的极限情形。

    python3 brainwallet.py
"""
import hashlib
import itertools
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section                              # noqa: E402
from btc import (privkey_to_pubkey, privkey_to_point, point_to_pubkey,  # noqa: E402
                 p2pkh, p2wpkh, N)

# 一个很小的「公开弱口令表」样本。真实的表有几十亿条
# （brainflayer 配套的表、泄露的密码库、维基语录、歌词、圣经句子……）
BASE = [
    "bitcoin", "satoshi", "password", "correct horse battery staple",
    "to be or not to be", "hello world", "test", "brainwallet",
    "let me in", "i am rich", "my secret passphrase", "qwerty",
    "the quick brown fox jumps over the lazy dog",
    "all your base are belong to us", "open sesame",
]
MUTATIONS = ["", "1", "123", "!", "2024", "2025"]


def candidates():
    """口令表 × 几个最常见的后缀 —— 真实攻击者的第一招。"""
    for base in BASE:
        for suf in MUTATIONS:
            yield base + suf
        yield base.capitalize()
        yield base.upper()


def brainwallet_addresses(passphrase: str):
    """
    脑钱包的全部内容就是这一行：

        私钥 = SHA256(口令)

    没有盐，没有 KDF，没有迭代。一次哈希。
    """
    k = int.from_bytes(hashlib.sha256(passphrase.encode()).digest(), "big")
    if not 0 < k < N:
        return None
    pt = privkey_to_point(k)                  # ← 只做一次标量乘法
    unc = point_to_pubkey(pt, compressed=False)
    com = point_to_pubkey(pt, compressed=True)
    return {
        "p2pkh_uncompressed": p2pkh(unc),     # 三种地址共用同一个点
        "p2pkh_compressed": p2pkh(com),
        "bech32": p2wpkh(com),
    }


def main():
    banner(7, "脑钱包（2009– ）",
           "不用随机数，直接把人想的一句话哈希一下当私钥。"
           "人能想出来的话，别人也能想出来 —— 而且已经列成表了。",
           "Milk Sad 研究更新 #16；Castellucci 的 brainflayer，DEF CON 23（2015）；"
           "Brain Drain 论文（2016）。")

    section("1 · 整个方案就是一行")
    for p in ["bitcoin", "satoshi", "correct horse battery staple"]:
        a = brainwallet_addresses(p)
        print(f"  口令 {p!r}")
        print(f"    私钥   {hashlib.sha256(p.encode()).hexdigest()}")
        print(f"    地址   {a['p2pkh_uncompressed']}  （未压缩，当年的默认）")
        print(f"           {a['bech32']}")

    section("2 · 字典爆破：给我一个地址，我还你口令")
    victim = "all your base are belong to us"       # 固定 demo 口令，在上面那张表里
    target = brainwallet_addresses(victim)["p2pkh_uncompressed"]
    print(f"  攻击者只看到链上一个地址: {target}")
    print("  他不知道口令，他只有一张表。开始跑：\n")
    t0 = time.perf_counter()
    found, tried = None, 0
    for c in candidates():
        tried += 1
        a = brainwallet_addresses(c)
        if a and target in a.values():
            found = c
            break
    dt = time.perf_counter() - t0
    print(f"  ✅ 口令 = {found!r}")
    print(f"     {tried} 次尝试，{dt * 1000:.0f} 毫秒，{tried / dt:,.0f} 候选/秒")
    print(f"\n  注意速率：**{tried / dt:,.0f} 候选/秒，纯 Python，一个核。**")
    print("  这里每个候选要做一次完整的椭圆曲线标量乘法 —— 最贵的那一步。")
    print("  用 C + GPU 的 brainflayer 做到每秒数十万到数百万。")

    section("3 · Reitter 那句话 —— 它解释的不止是脑钱包")
    print("""  > 你等于是把区块链当成一个巨大的公共密码哈希库，让所有人都可以
  > **离线、并行、零链上成本地**，同时爆破这一类型的所有钱包。

  三个词，每个都是一个坏消息，而且**对前面五课全部适用**：

    离线        —— 攻击者不碰你的设备、不碰你的网络、不碰任何你能看见的东西
    并行        —— 他不是在找你，他是在同时找所有人。
                   你的安全程度不取决于你多小心，取决于**生成你钥匙的那段代码**
    零链上成本  —— 没有失败的尝试会留下痕迹。
                   不像撞 PIN 码会锁死设备，这里试一万亿次没有任何代价

  **这就是为什么第 1 道门的失败是静默的。**
  门 2（设备）失败你知道 —— 东西丢了。
  门 3（签名）失败你看得见 —— 屏幕上地址不对。
  门 1 失败什么都看不出来，直到某一天余额是 0。""")

    section("4 · 「攻击者有多快」的基准")
    print("""  脑钱包给了整个类别一个时间基准：

      2015 年 Castellucci 在 DEF CON 23 公开 brainflayer
      → 这类钱包**基本立刻就被清空了**

  也就是说，「钥匙可被计算」到「钥匙真的被计算」的间隔 ≈ 0。
  这是第 13 课那张表的下限。对照一下：Cake Wallet 约 3 年，Ill Bloom 8–12 年。

  为什么脑钱包是 0 而别的是年？因为脑钱包**不需要先搞清楚是哪个软件**。""")

    section("5 · 最该注意的一条：2025 年还在发生")
    print("""  Milk Sad #16 里那个数字：

      1-轮-SHA256 范围里最近的一个高价值钱包
      bc1qskd34tec8fs04mmf0qzfjgq4e548ajc6ldqvex
      约 **$50 万（5.26 BTC）在 2025 年 2 月**流过它。
      **那个口令出现在公开的弱口令表里。**

  Reitter 说无法确定是否在入账后几秒内就被自动偷走，但「在我们看来非常可能」。

  → **2025 年还有人往一个用公开弱口令表里的词做的脑钱包里打 50 万美元。**
    brainflayer 公开十年了。**知识的传播比你想象的慢得多。**

  这一条是整个课程里最该让人谦虚的一句：
  这些漏洞不是因为难才存在，是因为**没人告诉用过它的那个人**。""")

    section("6 · 数字")
    print("""      3,606.59 BTC   SHA256 单轮范围的历史流量（主要是 BCH 硬分叉前的 BTC 使用）
      51.28 BTC      另一范围
      全是空的       Milk Sad 新找到的那些钱包 —— 这个类别已经被清干净了""")


if __name__ == "__main__":
    main()
