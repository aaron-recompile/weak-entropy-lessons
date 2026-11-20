#!/usr/bin/env python3
"""
第 4 课 · Trust Wallet 浏览器扩展 —— 2^32 到底有多小。

    python3 trust_wallet.py
"""
import hashlib
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section, fmt_dt                      # noqa: E402
from mt19937 import MT19937, first_bytes_high8                  # noqa: E402
from bip39 import entropy_to_mnemonic                           # noqa: E402


def wasm_random(seed32: int, nbytes=16) -> bytes:
    """
    2022-11 那个为 Wasm 目标新写的 "secure random generator"，形状是这样：

        std::mt19937 gen(seed);          // seed 是 32 位
        std::uniform_int_distribution<> d(0, 255);
        for (auto& b : buf) b = d(gen);

    为什么会有这个包装层：**Wasm 里读不到 /dev/urandom。**
    这个理由听起来完全合理 —— 这就是本课程的主题。
    """
    return first_bytes_high8(seed32, nbytes)


def main():
    banner(4, "Trust Wallet 浏览器扩展（CVE-2023-31290）",
           "一个 32 位的种子，就是一张 80 GB 的表。表做完了，破解一个钱包要 0.2 秒。",
           "Ledger Donjon 复盘，2023-04-25。本课唯一一个「审计发现」的案例：潜伏 3 天。")

    section("1 · 2^32 的物理量感")
    print(f"  2^32 = {2 ** 32:,} 个种子")
    print("""
  Ledger Donjon 真的把它做完了，而且把工程数字都公布了：

      2^32 个 ETH 地址全表            = 80 GB（压到种子 + 地址前 8 字节是 48 GB）
      硬件                            = 2 张 GTX 1080 Ti + OpenCL
      查 1,873,720 个地址             = 4 分 22 秒
      给 3 个测试地址反推出助记词     = 0.2 秒

  Donjon 自己的结论最该记住：
      **快到足以实时处理以太坊全链交易，在弱地址一被使用的瞬间就破掉它。**
  ——也就是监听 mempool，钱还没确认，私钥已经算出来了。""")

    section("2 · 在本机做一张迷你版的表，看看机理")
    TABLE_BITS = 17
    n = 1 << TABLE_BITS
    print(f"  建表：枚举 2^{TABLE_BITS} = {n:,} 个种子，每个存「熵的前 8 字节 → 种子」")
    t0 = time.perf_counter()
    table = {}
    for s in range(n):
        table[wasm_random(s, 8)] = s
    dt = time.perf_counter() - t0
    per_sec = n / dt
    size_per_entry = 8 + 4
    print(f"  用了 {dt:.1f} 秒（{per_sec:,.0f} 个/秒，纯 Python 单核）")
    print(f"  这张表占 {n * size_per_entry / 1e6:.1f} MB")
    full = 2 ** 32 * size_per_entry
    print(f"  同样格式的全表（2^32）= {full / 1e9:.1f} GB  ← 和 Donjon 的 48 GB 同一个量级")
    print(f"  本机建全表要 {fmt_dt(2 ** 32 / per_sec)}；他们用 2 张 1080 Ti 做完了。")

    section("3 · 表做完之后：查表是 O(1)")
    victim_seed = 0xBEEF  # 固定 demo 种子
    victim_ent = wasm_random(victim_seed, 16)
    print(f"  demo 受害者（虚构，固定种子 0x{victim_seed:X}）")
    print(f"  助记词: {entropy_to_mnemonic(victim_ent)}")
    t0 = time.perf_counter()
    hit = table.get(victim_ent[:8])
    dt = time.perf_counter() - t0
    print(f"\n  查表: 种子 = {hit}（0x{hit:X}），耗时 {dt * 1e6:.1f} 微秒")
    print(f"  重算一遍验证: {entropy_to_mnemonic(wasm_random(hit, 16)) == entropy_to_mnemonic(victim_ent)}")
    print("""
  **这是弱熵最可怕的那个性质：成本结构是「一次性建表 + 之后永久免费」。**
  Donjon 的 0.2 秒不是因为他们算得快，是因为表已经在那了。
  而表一旦存在，它不会过期 —— 第 13 课那个「武器库」就是这个意思。""")

    section("4 · 时间线：唯一一次防守方赢了")
    print("""      2022-11-14   扩展发布
      2022-11-17   Ledger Donjon 报给币安赏金计划        ← 3 天
      2022-11-21   Trust Wallet 在 GitHub 上公开提交修复
                   （Donjon 原话：「我们当时很担心有人会注意到它并利用这个漏洞」
                     —— 修复先于披露公开提交，本身就是一次竞速）
      2023-03      拿到最高档赏金 $10 万
      2023-04-22   公开披露 + 复盘。此时仍有约 $10 万可被直接偷走
      发布后几天内 约 $3,000 万一度在险

  **11 个案例里，这是唯一一个「在任何人被偷之前」就被关掉的。**
  原因只有一个：有人在新产品发布的时候主动去看了。
  其余 10 个的潜伏期全部以年计 —— 最长 12 年。""")

    section("5 · Donjon 在 2023 年写下的那句预言")
    print("""  > 调查中我们还注意到，有少数地址是脆弱的，但它们的生成时间**远早于**
  > Trust Wallet 扩展发布。这大概意味着这个漏洞还存在于**其他某些钱包实现**里，
  > 这很令人担忧……

  两年后，Reitter 在 2026-03 的研究更新 #19 里找到了那个东西：
  **一个 2018 年的、至今没人知道是哪个的软件**，13.7 万枚 BTC 的量级。
  两个独立团队，从两端收敛到同一个结论。见第 13 课。""")

    section("6 · 同一家公司，三次")
    print("""  | 版本        | 时间    | 机理                                              | CVE            |
  |-------------|---------|---------------------------------------------------|----------------|
  | iOS 变体 A  | 2018 中 | 用了 trezor-crypto 里**标注不供生产使用**的函数    | CVE-2024-23660 |
  |             |         | 31 位状态，srand(time(NULL)) 播种                 |                |
  | iOS 变体 B  | 2018 中 | 同上，另一个变体                                  | 同上           |
  | 浏览器扩展  | 2022-11 | 为 Wasm 新写的 std::mt19937 包装，32 位种子       | CVE-2023-31290 |

  三次的直接原因都不一样，三次的形状完全一样：**在系统随机数接口外面包了一层。**
  iOS 那两个是 SECBIT Labs 在查 2023-07-12 那批盗案时倒推出来的 —— 见第 13 课，
  那一天 bx 的钱包和 Trust Wallet iOS 的钱包**被同一批人在同一天扫了**。

  （证据：iOS 的 ≥6,572 个助记词是经 Milk Sad #5 转述 SECBIT 的，
   Milk Sad 自己标注为「初步、不完整」。我没有读 SECBIT 原文。）""")


if __name__ == "__main__":
    main()
