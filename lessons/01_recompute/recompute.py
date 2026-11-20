#!/usr/bin/env python3
"""
第 1 课 · 不是碰撞，是重算。

    python3 recompute.py
"""
import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section                              # noqa: E402
from bip39 import entropy_to_mnemonic                           # noqa: E402
from btc import privkey_to_point, point_to_pubkey, p2wpkh       # noqa: E402

M32 = 0xFFFFFFFF


def weak_wallet(seed32):
    """
    一个弱钱包生成器，缩到十行。它做的事情和真实案例一模一样：
    32 位种子 → 确定性的字节流 → 助记词 → 私钥 → 地址。
    注意：**这里面没有任何一步是「猜」。** 全是正向计算。
    """
    s, out = seed32 & M32, bytearray()
    while len(out) < 32:
        s ^= (s << 13) & M32
        s ^= s >> 17
        s ^= (s << 5) & M32
        out += s.to_bytes(4, "big")
    return bytes(out[:32])


def strong_wallet():
    return os.urandom(32)


def to_address(entropy):
    """熵 → 地址。钱包当年走的就是这条路，攻击者走的也是同一条。"""
    k = int.from_bytes(hashlib.sha256(entropy).digest(), "big")
    return p2wpkh(point_to_pubkey(privkey_to_point(k)))


def main():
    banner(1, "不是碰撞，是重算",
           "攻击者不是在猜你的钥匙。他是在**重新运行当年生成你钥匙的那段代码**。",
           "Coinspect / Milk Sad 的全部方法论都建立在这个区分上。"
           "本课是后面十三课的第一性原理。")

    section("1 · 先把两个词分开 —— 它们完全不是一回事")
    print("""  **碰撞**：两个不同的输入，落到同一个输出上。
            「别人的钥匙恰好对上了你的地址。」

  **重算**：攻击者跑同一个程序，拿到**字节级完全相同**的那把钥匙。
            不是「对上了」，是**同一把**。

  几乎所有人第一反应想的是碰撞。而碰撞在比特币上根本不会发生。
  真正发生的全部是重算。下面两段代码分别证明这两句话。""")

    section("2 · 碰撞：算一下它有多不可能")
    bits = 160                      # 地址是 HASH160，160 位
    n = 10 ** 9                     # 假设历史上一共产生过十亿个地址（高估）
    space = 2 ** bits
    p = n * n / (2 * space)         # 生日问题近似
    print(f"  地址空间            2^{bits} = {space:.3e}")
    print(f"  历史上的地址总数    约 {n:.0e}（高估）")
    print(f"  任意两个相撞的概率  约 {p:.2e}")
    print(f"\n  参考：你连续 {math.log(1 / p) / math.log(6):.0f} 次掷骰子全掷到 6，概率比这个还大。")
    print("\n  → **碰撞不是风险。** 不管谁跟你说什么，这条路是关着的。")

    section("3 · 重算：同一个程序，两次运行")
    DEMO_SEED = 0x5EED1234          # 固定的 demo 种子，纯演示
    a = weak_wallet(DEMO_SEED)
    b = weak_wallet(DEMO_SEED)
    print(f"  第一次运行: {entropy_to_mnemonic(a).split()[0:4]} ...")
    print(f"  第二次运行: {entropy_to_mnemonic(b).split()[0:4]} ...")
    print(f"  字节级相同: {a == b}")
    print(f"  地址也相同: {to_address(a) == to_address(b)}  ({to_address(a)})")
    print("""
  这**不是**碰撞 —— 没有两个不同的输入。只有一个输入，跑了两次。
  当年钱包跑了一次，今天攻击者跑了第二次。仅此而已。""")

    section("4 · 对照：强随机数下，「第二次」不存在")
    xs = [strong_wallet() for _ in range(3)]
    for i, x in enumerate(xs, 1):
        print(f"  第 {i} 次: {entropy_to_mnemonic(x).split()[0:4]} ...")
    print(f"  有任何两次相同吗: {len(set(xs)) != len(xs)}")
    print("""
  区别不在于「强随机数更难猜」。区别在于：
  **弱随机数有一个可以被重新喂进去的输入（种子），强随机数没有。**
  os.urandom 没有种子参数 —— 你没法要求它「再给我一次上次那个」。""")

    section("5 · 攻击是**正向**跑的 —— 这一条推翻很多直觉")
    print("  攻击者走的每一步，都和钱包当年走的完全一样，方向也一样：\n")
    ent = weak_wallet(DEMO_SEED)
    k = int.from_bytes(hashlib.sha256(ent).digest(), "big")
    pub = point_to_pubkey(privkey_to_point(k))
    steps = [("① 种子", f"0x{DEMO_SEED:08X}"),
             ("② 熵（32 字节）", ent.hex()[:32] + "…"),
             ("③ 私钥", f"{k:064x}"[:32] + "…"),
             ("④ 公钥", pub.hex()[:32] + "…"),
             ("⑤ 地址", to_address(ent))]
    for name, v in steps:
        print(f"    {name:<18} {v}")
    print("""
  注意箭头的方向：①→②→③→④→⑤，**从头到尾都是往下走的**。

  攻击者**从来不需要**：
    ✗ 看你的公钥           ✗ 做任何密码分析
    ✗ 从地址逆推回公钥     ✗ 从公钥逆推回私钥
    ✗ 攻破 secp256k1       ✗ 攻破 SHA-256 或 RIPEMD-160

  他只在最后一步用你的地址做一次**查表比对**：
  「我算出来的这五亿个地址里，有没有一个在链上有钱？」""")

    section("6 · 三个推论，每个都反直觉")
    print("""  ① **「比特币的密码学没有被攻破」和「你的钱没了」可以同时为真。**
     而且历史上每一次都是同时为真。椭圆曲线一次都没坏过。

  ② **量子计算和这件事无关。**
     量子打的是「公钥暴露之后，能不能逆推回私钥」—— 那是一个**逆向**问题。
     重算根本不需要逆向，所以抗量子签名方案一个字节都修不了弱熵。
     （反过来也成立：你把弱熵修好了，量子那条线一点没动。两条线互不替代。）

  ③ **换算法、换曲线、加长地址、加长助记词，全都不修这个。**
     因为缺陷不在密码学里，在**生成器**里。
     第 10 课会让你看到，连 2048 轮 PBKDF2 也不修 —— 它拉伸的是已经弱掉的那个数。""")

    section("7 · 所以第 1 道门只有一个问题")
    print("""  既然攻击就是「重新跑一遍当年那段代码」，那么你需要回答的只有一句：

        **这批词，是哪段代码生成的？**

  只有两种答案：

    ✅ 「在一台可信设备上、由设备自己生成的，而且我掷了足够多的私密骰子」
       → 门关着。这是唯一在 Coldcard 事故里被证明有效的答案（第 8 课）。

    ⚠️  其他任何答案 —— 在电脑上生成再录进设备、用过某个命令行工具、
       从某个 App 导出的、几把钥匙来自同一次生成、记不清了
       → **门的状态是未知的，而未知在这件事上等于不安全**，因为失败是静默的。

  后面十三课，全部是这一句话的展开。""")


if __name__ == "__main__":
    main()
