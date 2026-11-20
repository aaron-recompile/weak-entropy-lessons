#!/usr/bin/env python3
"""
第 3 课 · CryptoJS / Ill Bloom —— 一个坏掉的随机数，活了 12 年。

    python3 ill_bloom.py
    node cryptojs_random.js zero 16     # 原版 JS，同一个结果
"""
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
from lesson import banner, section                              # noqa: E402
from bip39 import entropy_to_mnemonic                           # noqa: E402

MASK = 0xFFFFFFFF


def i32(x):
    """JS 的 ToInt32：所有位运算都先过这一步，结果是有符号的。"""
    x = int(x) & MASK
    return x - 0x100000000 if x & 0x80000000 else x


def cryptojs_random(nbytes, math_random):
    """
    CryptoJS 3.x 的 WordArray.random，逐行对照 JS 翻过来。

    只有一个地方有熵：math_random()。
    m_z 的初值 0x3ade68b1 是**硬编码的常量**，不是随机的。
    """
    words = []
    rcache = None

    def make_r(m_w_init):
        state = {"m_w": i32(m_w_init), "m_z": 0x3ADE68B1}

        def nxt():
            state["m_z"] = i32(0x9069 * (state["m_z"] & 0xFFFF) + (i32(state["m_z"]) >> 16))
            state["m_w"] = i32(0x4650 * (state["m_w"] & 0xFFFF) + (i32(state["m_w"]) >> 16))
            result = i32(i32(state["m_z"] << 16) + state["m_w"])
            result = result / 0x100000000
            result += 0.5
            return result * (1 if math_random() > 0.5 else -1)
        return nxt

    i = 0
    while i < nbytes:
        _r = make_r((rcache if rcache else math_random()) * 0x100000000)
        rcache = _r() * 0x3ADE67B7
        words.append(i32(_r() * 0x100000000))
        i += 4
    return words


def words_to_bytes(words, nbytes):
    buf = b"".join(struct.pack(">i", w) for w in words)
    return buf[:nbytes]


def gen(nbytes, math_random):
    return words_to_bytes(cryptojs_random(nbytes, math_random), nbytes)


def main():
    banner(3, "CryptoJS / Ill Bloom（CVE-2026-71851）",
           "自造的随机数生成器，唯一的熵来自 Math.random()，而它只收得下 32 位。"
           "第一个助记词以 illness blossom 开头 —— 漏洞名字就是这么来的。",
           "Coinspect illbloom.org；Milk Sad #20/#21/#22。潜伏 12 年（2014 → 2026-05）。"
           "攻击者 2026-05-27 先动手，研究者 2026-06-10 才上报。")

    section("1 · Math.random() 返回 0 的时候")
    ent = gen(16, lambda: 0.0)
    mn = entropy_to_mnemonic(ent)
    print(f"  熵（16 字节）: {ent.hex()}")
    print(f"\n  {mn}\n")
    print(f"  前两个词: {' '.join(mn.split()[:2])}  ←  Ill Bloom 这个名字的来源")

    section("2 · 和原版 JS 对一下 —— 不是我重写的，是同一段代码")
    try:
        out = subprocess.run(["node", os.path.join(HERE, "cryptojs_random.js"), "zero", "16"],
                             capture_output=True, text=True, timeout=30, check=True)
        import json
        js = json.loads(out.stdout)
        print(f"  node（原版 crypto-js 代码）: {js['hex']}")
        print(f"  Python（本课的移植）      : {ent.hex()}")
        print(f"  逐字节一致: {js['hex'] == ent.hex()}")
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        print(f"  （没装 node，跳过交叉验证：{e}）")

    section("3 · 熵在哪里漏掉的 —— 这一段是本课的核心")
    print("""  那个生成器有两个状态字：

      m_z = 0x3ade68b1      ← 硬编码的常量。零熵。
      m_w = Math.random() * 2^32   ← 唯一的熵入口

  而 m_w 进来之后立刻被 `& 0xFFFF` 和 `>> 16` 切成两半用 —— 也就是说
  **只有整数部分的低 32 位有用**。Math.random() 本来有 52 位尾数，剩下 20 位直接扔了。""")
    base = 0.123456789012345
    eps = 2.0 ** -45                    # 远小于 2^-32 的一步
    a = gen(16, lambda: base)
    b = gen(16, lambda: base + eps)
    print(f"\n  实证：Math.random() = {base}")
    print(f"       Math.random() = {base + eps}（差 2^-45）")
    print(f"       输出 a: {a.hex()}")
    print(f"       输出 b: {b.hex()}")
    print(f"       一样吗: {a == b}  ← 超出 32 位的那些尾数位，确实被扔掉了")

    section("4 · 数一下总共剩多少位")
    print("""  每次调用 `_r()` 末尾有一个 `Math.random() > .5 ? 1 : -1` —— 那是 1 个符号位。
  而每生成一个 32 位字，`_r()` 被调两次。于是：

      128 位请求（4 个字）：32 位（初始 m_w） + 4×2 位（符号） = 40 位
      256 位请求（8 个字）：32 位            + 8×2 位         = 48 位

  Coinspect 公布的实测口径是 **~2^39** 和 **~2^47** —— 和上面这个纸上推演各差约 1 位
  （首字的低位有一部分结构性塌缩，见下面那个 0000）。量级对得上。""")
    print(f"\n  顺手看一眼那个塌缩：Math.random()=0 时的首字是 {ent.hex()[:8]}"
          f" —— 低 16 位是 0000，不是巧合。")
    print("\n  **本该是 128 位。实际是 40 位。而代码里没有一行是「写错的密码学」。**")

    section("5 · 这一课真正的教训不在代码里")
    print("""  Ill Bloom 有一个别的案例都没有的细节：

      crypto-js 的 3.2.0 / 3.2.1 **已经修好了** —— 换成了系统的密码学随机源。
      但 3.3.0 又把弱代码**恢复**了，理由是那个改动被认为是 breaking change。
      最终到 4.0.0 才真正修好。

  **这不是编码失误，是组织决策失误。「向后兼容」压过了「密码学正确」。**
  这类失效模式，AI 写代码一点都不会改善 —— 它甚至会更乐意保持向后兼容。

  （证据分级：版本史是二手转述，「回退是因为被认为 breaking change」这个因果
   我没读到 crypto-js 的原始 issue。机理是硬的，这条归因是软的。）""")

    section("6 · 规模")
    print("""  Reitter 一手验证的下界（仅 BTC / 128 位 / 英文词表）：
      795 个钱包、986 个用过的地址、8,120.9 BTC / 约 $1.001 亿历史流量，最早活动 2018-09
  Coinspect 口径的实际被盗：截至 2026-07-13 约 $569 万（自称下界）
  弱钱包里的余额在 2026-05-27 和 2026-07-10 两次事件中从约 $300 万掉到零
  Coinspect 明确说：**硬件钱包用户不受 Ill Bloom 影响。**

  已确认受影响的 App 五个（Coinspect 自己说「只是目前已确认的，不是完整名单」）：

      RRWallet（人人比特）  已停运    **无修复**
      Bexo Wallet           在运营    20.1.0 已修
      NanChat               在运营    1.3.0 已修（带迁移机制）
      Bitcoin Libre         在运营    第 4 版已修（2024-07）
      Milo                  已停运    **无修复**

  两个「已停运、无修复」值得单独看一眼：**软件可以停运，弱种子不会停运。**""")

    section("7 · 中文助记词那件事 —— 按真实尺寸讲")
    print("""  有一篇专门的「中文助记词盗转分析」，很容易被放大成
  「中文钱包有独立的缺陷」。把数字摆出来就清楚了：

      中文词表子集                142 个种子（比特币 / 以太坊 / 波场）
      2026-07-20 至 07-21 被扫    81 个
      合计损失                    **约 $38,563**
      对照 Ill Bloom 两次主事件   约 $5.69M

  占比 **0.68%**。

  → **它证明的不是「中文钱包更危险」，而是「攻击者会枚举非英语词表」。**
    这是一条关于**攻击者覆盖面**的证据，不是一条关于中文生态的证据。

  真正有信息量的细节在别处：那批以太坊盗转**汇集到两个之前就出现过的
  收款地址**上 —— 同一套收款基础设施，跨链协同执行。
  这是把它和主事件绑在同一场战役里的硬证据，也是第 13 课「武器库」那条的佐证。

  出处：illbloom.org/articles/chinese-mnemonic-drains/（本课已读原文）""")


if __name__ == "__main__":
    main()
