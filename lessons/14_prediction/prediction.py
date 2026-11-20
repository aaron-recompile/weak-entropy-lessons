#!/usr/bin/env python3
"""
第 14 课 · 一个可证伪的赌注。

    python3 prediction.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
from lesson import banner, section, pad                         # noqa: E402

WRAPPERS = [
    ("2011–2015", "BitcoinJS（Randstorm）", "SecureRandom()，来自 JSBN 库", "浏览器里没有系统 CSPRNG"),
    ("2012–2018", "PHPCoinAddress", "直接用 PHP 的 mt_rand()", "PHP 当年没给好用的 CSPRNG"),
    ("2014–2026", "CryptoJS（Ill Bloom）", "WordArray.random()，自造 MWC", "JS 里没有统一的 CSPRNG"),
    ("2018", "Trust Wallet iOS", "trezor-crypto 里标注「不供生产」的函数", "赶工"),
    ("2020–2021", "Cake Wallet", "自己写的 randomBytes(len, {secure=false})", "图方便，而且默认不安全"),
    ("2021–2026", "Coldcard", "libngu 的 ngu.random，链接期绑 rng_get", "想换掉外部依赖"),
    ("2022", "Trust Wallet 扩展", "为 Wasm 新写的 std::mt19937 包装", "**Wasm 里读不到 /dev/urandom**"),
]

PLATFORMS = ["浏览器", "PHP / 服务器", "移动端", "Wasm", "React Native"]
CANDIDATES = [
    ("嵌入式 / IoT 签名器", "最可能", "新芯片、新 SDK，第一版总是先凑一个随机数出来"),
    ("浏览器扩展的新运行时", "可能", "2022 年那次就是运行时换代（Wasm）"),
    ("AI 生成的钱包代码", "可能，但零一手证据", "它最爱干的事就是写一个「看起来对」的包装层"),
]


def main():
    banner(14, "一个可证伪的赌注",
           "十三年，十一个独立案例，十一个不同的团队，没有一次把密码学写错。"
           "每一次都是在操作系统的随机数接口外面包了一层 —— "
           "而每个包装层都有一个听起来合理的理由。",
           "案例库 §1.4 和 §9.8。Coinspect 给开发者的两条建议是这张表的逆否命题。")

    section("1 · 大白话：这个课程只有一个发现")
    print("""  我们看了十一个案例。你可能以为它们的共同点是「随机数很难」。

  不是。它们的共同点比这个具体得多，也有用得多：

      **bug 从来没有一次出在密码学里。**
      **每一次都出在一个「为了绕开操作系统的随机数接口而写的包装层」里。**

  而且每个包装层都有一个**听起来完全合理的理由**。
  这是最关键的一句 —— 这些不是蠢人写的蠢代码，是聪明人面对一个真实约束
  做出的合理反应。""")

    section("2 · 证据：一行一个")
    print("  " + pad("年份", 12) + pad("案例", 24) + pad("那个包装层", 44) + "为什么会有它")
    print("  " + "-" * 110)
    for y, case, wrapper, why in WRAPPERS:
        print("  " + pad(y, 12) + pad(case, 24) + pad(wrapper, 44) + why)

    section("3 · Coinspect 的两条建议 —— 它就是上面那张表的逆否命题")
    print("""  > 熵必须**直接**来自操作系统提供的那个密码学安全接口。
  > **避免在随机数生成外面加任何不必要的包装层** —— 它们会引入意外的 fallback、
  > 平台相关的行为、以及微妙的类型转换，在没有明显症状的情况下削弱安全性。
  >
  > 随机数失败必须被当成**致命错误**。钱包创建应当直接中止，
  > 而不是退化到非密码学的随机源。

  注意第二条。它说的是：**「优雅降级」在这件事上是一个 bug，不是一个特性。**
  第 11 课那五道保险，全都是在给一个已经降级了的系统做体检。""")

    section("4 · 赌注")
    print("  平台序列（历史）：" + " → ".join(PLATFORMS))
    print("""
  **预测：下一次弱熵事故会出现在一个新平台上。**

  机理：新平台总是**先没有好的随机数接口，然后有人写包装层**。
  这个顺序在过去二十年重复了五次。

  今天的候选：
""")
    for name, odds, why in CANDIDATES:
        print("  " + pad("· " + name, 26) + pad(odds, 20) + why)
    print("""
  **这个预测怎么被证伪：**

    ✗ 如果下一次事故出在一个老平台的老库里（比如又一个 2014 年的 JS 库），
      「新平台」这个机理就是错的 —— 真正的变量是「老代码没人看」。
    ✗ 如果下一次事故的根因真的是密码学本身写错了（比如一个 secp256k1 实现的
      边界条件），那「永远是包装层」这句话就破了。
    ✗ 如果三年内没有新的弱熵事故，那「1–2 个/年、十三年没下降」这个基率就变了。

  **这三条都可以在不问任何人的情况下核实。** 这是这个预测唯一的价值。""")

    section("5 · 关于 AI 的那一条：先说清楚它现在是什么地位")
    print("""  ⚠️  **目前没有任何一个已知案例的坏包装层是 AI 写的。零一手证据。**

  这个预测是从十一个案例的共同形状**外推**的，不是观察到的。
  它可被证伪，这是它的优点，也是它目前唯一的地位。

  为什么我仍然把它列为候选，两条理由，都不是「AI 很危险」这种话：

  ① **形状吻合。** 十一个案例的共同形状是「写一个看起来对的包装层」，
     而这恰好是语言模型最擅长、也最容易出错的事情 —— 它会生成
     惯用、通过代码评审、在测试里跑得通的代码。弱熵正是那种
     「惯用、通过评审、测试跑得通」的 bug。

  ② **第 3 课那个细节。** crypto-js 的弱代码在 3.2.0 修好过，
     3.3.0 又被**恢复**了，理由是「破坏向后兼容」。
     **这不是编码失误，是组织决策失误。** AI 写代码一点都不会改善这个 ——
     它甚至会更乐意保持向后兼容。

  而反方向的一条证据，也必须说：
  **上游 session 专门找过「AI 生成的加密货币恶意软件」的一手证据，找不到。**
  2025–2026 所有真实被盗案的机理都是 2018 年之前就存在的技术。
  AI 唯一有记录的、对比特币安全的实际贡献，**是在防守侧**。""")

    section("6 · 这一课可以自己做的实验")
    print("""  同目录下有两个东西：

      audit_wallet_code.py     把那十一个案例的形状写成了 10 条规则的嗅探器
      collect_ai_samples.md    一个你自己能跑的取样实验（含确切的 prompt）

  先看嗅探器能不能抓住历史案例（这是它的回归测试）：
""")
    samples = os.path.join(HERE, "samples")
    r = subprocess.run([sys.executable, os.path.join(HERE, "audit_wallet_code.py")]
                       + sorted(os.path.join(samples, f) for f in os.listdir(samples)
                                if not f.endswith(".md")),
                       capture_output=True, text=True)
    bad_caught = r.stdout.count("🔴") + r.stdout.count("🟠") + r.stdout.count("🟡")
    good_clean = r.stdout.count("没有命中任何")
    print(f"      6 个「坏」样本（历史案例转录）→ 命中 {bad_caught} 条规则")
    print(f"      2 个「好」样本（直接用系统 CSPRNG）→ {good_clean} 个干净")
    print(f"\n      完整输出：python3 audit_wallet_code.py samples/*")
    print("""
  然后是那个取样实验：**让模型写「生成 BIP39 助记词」的代码，看它写出什么。**
  规程、prompt、记录表都在 collect_ai_samples.md 里。

  **这个实验的结果我没有，所以课程里没有结论。** 等你跑完，结论才存在。""")

    section("7 · 整个课程压缩成两句")
    print("""  **十三年，十一个独立案例，十一个不同的软件团队，没有一次把密码学写错，
  每一次都是在操作系统的随机数接口外面包了一层。**

  **最偏执的那台设备（Coldcard）用五道保险去防这件事，五道全部失效，
  因为它们都在检查输出，而出问题的是来源。
  唯一活下来的用户，是那些不相信设备、自己掷了五十次骰子的人。**""")


if __name__ == "__main__":
    main()
