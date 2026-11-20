#!/usr/bin/env python3
"""
第 10 课 · PBKDF2 救不了你 —— 乘法性的单次成本，补不回几十位熵的损失。

    python3 pbkdf2_wont_save_you.py
"""
import hashlib
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section, fmt_dt, vs_universe, pad     # noqa: E402
from bip39 import entropy_to_mnemonic, mnemonic_to_seed          # noqa: E402
from btc import privkey_to_point, point_to_pubkey, p2pkh, derive_path  # noqa: E402

GPU_PER_SEC = 1_500_000


def main():
    banner(10, "PBKDF2 救不了你",
           "BIP39 的 2048 轮 PBKDF2 只是把每个候选变贵一点，它不恢复丢掉的熵 —— "
           "因为攻击走的不是助记词空间，是生成器的状态空间。",
           "Wizardsardine 2026-08-11 的原话：「攻击并不是在 2^128 个助记词里走，"
           "它是在生成器的状态空间里走。在那个尺度上，PBKDF2 只是把秒变成分钟。」")

    section("1 · 大白话：一个很常见的直觉，它是错的")
    print("""  那个直觉是：「就算熵弱一点，可是 BIP39 还有 2048 轮 PBKDF2 拉伸啊，
  攻击者每试一个候选都要付这个代价，所以还是很贵。」

  这句话的前半句对，后半句错。为什么：

      KDF 是**乘法性**的 —— 它把每个候选的成本乘上一个常数 C。
      熵是**指数性**的 —— 它决定候选的**个数** 2^n。

      总成本 = C × 2^n

  丢掉 96 位熵，是把 2^n 从 2^128 变成 2^32。
  要靠 C 补回来，C 得等于 2^96 —— 那意味着你自己每次解锁钱包也要等 2^96 份时间。

  **KDF 是按线性收费的保险，熵是按指数收费的保险。它们不在一个量级上。**""")

    section("2 · 把 C 量出来")
    ent = bytes(range(32))                       # 固定的 demo 熵，纯演示
    mn = entropy_to_mnemonic(ent)
    n = 200
    t0 = time.perf_counter()
    for i in range(n):
        mnemonic_to_seed(mn)
    kdf = (time.perf_counter() - t0) / n

    t0 = time.perf_counter()
    for i in range(n):
        hashlib.sha256(ent + i.to_bytes(4, "big")).digest()
    raw = (time.perf_counter() - t0) / n

    print(f"  BIP39 的 2048 轮 PBKDF2-HMAC-SHA512，一个候选: {kdf * 1e6:,.0f} 微秒")
    print(f"  一次裸 SHA-256（纸钱包那条路的量级）  : {raw * 1e6:,.1f} 微秒")
    print(f"\n  C = {kdf / raw:,.0f} 倍 ≈ 2^{math.log2(kdf / raw):.1f}")
    print(f"\n  **C 大约值 {math.log2(kdf / raw):.0f} 位熵。就这么多。**")
    print("  2048 轮听起来很多，它买到的是十来位。而弱熵一次丢掉的是几十位到一百位。")

    section("3 · 要多少轮才能补回 Coldcard Mk3 丢掉的那些？")
    mk3 = 2 ** 22
    target = 2 ** 128
    need = target / mk3
    print(f"  Mk3 的搜索空间     2^22 = {mk3:,}")
    print(f"  本该有的           2^128")
    print(f"  缺口               2^106 = {need:.3e}")
    print(f"\n  要让 2^22 个候选的总成本等于 2^128，每个候选得花 2^106 份工作量。")
    print(f"  按本机 PBKDF2 的单次耗时折算，需要的迭代轮数：")
    print(f"      2048 × 2^106 ≈ {2048 * need:.2e} 轮")
    print(f"  而你自己每次用这个钱包解锁，也要等同样的时间："
          f"{vs_universe(kdf * need)}")
    print("\n  → **这不是「调大一点就好了」，这是在要求一个物理上不存在的 KDF。**")

    section("4 · Mk3 的实际算例")
    print(f"  Wizardsardine 的实测：单张 RTX 4090，**约 150 万个完整候选/秒**，")
    print(f"  而且这个 150 万**已经包含了** BIP39 的 PBKDF2、BIP32 派生和地址查表。")
    print(f"\n      2^22 / 150 万 = **{2 ** 22 / GPU_PER_SEC:.1f} 秒**")
    print(f"      租用成本（$0.30/小时）= ${2 ** 22 / GPU_PER_SEC / 3600 * 0.30:.6f}")
    print("\n  **PBKDF2 在场的情况下，3 秒。** 这就是「只是把秒变成分钟」的字面意思。")

    section("5 · 跑一遍完整的攻击链，看 PBKDF2 在哪一环")
    t0 = time.perf_counter()
    seed = mnemonic_to_seed(mn)
    t1 = time.perf_counter()
    k, _ = derive_path(seed, "m/84'/0'/0'/0/0")
    t2 = time.perf_counter()
    addr = p2pkh(point_to_pubkey(privkey_to_point(k)))
    t3 = time.perf_counter()
    print(f"  ① 助记词 → 种子（PBKDF2 2048 轮）  {(t1 - t0) * 1000:8.2f} 毫秒")
    print(f"  ② 种子 → 私钥（BIP32，5 层派生）    {(t2 - t1) * 1000:8.2f} 毫秒")
    print(f"  ③ 私钥 → 地址（椭圆曲线 + 哈希）    {(t3 - t2) * 1000:8.2f} 毫秒")
    print(f"\n  本机上最贵的一环是 {'①' if (t1-t0) > max(t2-t1, t3-t2) else ('②' if (t2-t1) > (t3-t2) else '③')}。")
    print("  在优化过的 GPU 实现里，这三步的相对成本会变，但**总和仍然是个常数** ——")
    print("  而常数乘上 2^22 还是小，乘上 2^128 还是大。候选个数是唯一重要的量。")

    section("6 · 三个推论，都该记住")
    print("""  ① **纸钱包比助记词便宜得多。**
     纸钱包的私钥是生成器的**原始输出**，不走 PBKDF2，也不走 BIP32 ——
     测一个候选只要一次曲线乘法加一次哈希。
     所以在同一个弱熵事故里，纸钱包那批先被清。

     不拿 PBKDF2 和裸哈希比（那样会夸大），拿**两条完整的候选链**比：""")
    reps = 8
    t0 = time.perf_counter()
    for i in range(reps):
        k2 = int.from_bytes(ent[:31] + bytes([i]), "big")
        p2pkh(point_to_pubkey(privkey_to_point(k2)))
    paper = (time.perf_counter() - t0) / reps
    t0 = time.perf_counter()
    for i in range(reps):
        sd = mnemonic_to_seed(entropy_to_mnemonic(ent[:31] + bytes([i])))
        kk, _ = derive_path(sd, "m/84\'/0\'/0\'/0/0")
        p2pkh(point_to_pubkey(privkey_to_point(kk)))
    mnemo = (time.perf_counter() - t0) / reps
    print(f"       纸钱包一个候选（私钥 → 地址）        {paper * 1000:8.2f} 毫秒")
    print(f"       助记词一个候选（PBKDF2 + BIP32 + 地址）{mnemo * 1000:8.2f} 毫秒")
    print(f"       比值 {mnemo / paper:,.1f} 倍 ≈ 值 2^{math.log2(mnemo / paper):.1f} 位熵")
    print(f"""
     两种量法，两个上下界，结论同一个：

         只比 KDF 那一步（PBKDF2 vs 裸哈希）    {kdf / raw:>8,.0f} 倍 = {math.log2(kdf / raw):.0f} 位
         比完整候选链（本机实测）                {mnemo / paper:>8,.1f} 倍 = """
          f"""{math.log2(mnemo / paper):.0f} 位

     **上界十位，下界两位。无论怎么量，它都是个「十位以内」的常数。**
     而弱熵一次丢掉的是 96 位。本机是纯 Python，GPU 实现里比例会变，
     但「常数 vs 指数」这个性质不会变。""")
    print("""
  ② **强 passphrase 是唯一一个真正在这张表之上「再乘一个空间」的东西。**
     注意「乘一个空间」和「乘一个常数」的区别 —— passphrase 加的是**位**，
     KDF 加的是**倍**。这是本课唯一一条有用的防御建议。

     Wizardsardine 的那张爆破成本表**假设 passphrase 是空的**。
     一个强的、未知的 passphrase 会在整张表之上再乘一个搜索空间。

  ③ **BIP-85 恰好等于父种子的价值。** 它是确定性派生的，
     所以父种子弱 = 所有 BIP-85 子钱包一起弱。
     这条很容易被漏掉，因为 BIP-85 给人一种「每个子钱包独立」的错觉。""")


if __name__ == "__main__":
    main()
