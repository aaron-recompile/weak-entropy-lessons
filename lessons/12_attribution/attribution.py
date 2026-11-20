#!/usr/bin/env python3
"""
第 12 课 · 从链上反推到是哪个软件。

    python3 attribution.py
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
from lesson import banner, section, pad                         # noqa: E402

# Coinspect 已确认的五个（illbloom.org/articles/identifying-wallets-vulnerable-recovery-phrases/）
CONFIRMED = [
    ("RRWallet（人人比特）", "已停运", "无修复", "公开源码 + Arkham 实体标注"),
    ("Bexo Wallet", "在运营", "20.1.0 已修", "厂商被盗后主动找上门"),
    ("NanChat", "在运营", "1.3.0 已修（带迁移机制）", "npm 依赖链 → 追进生成流程"),
    ("Bitcoin Libre", "在运营", "第 4 版已修（2024-07）", "链上活动 → 开发者 Twitter → 本人确认"),
    ("Milo", "已停运", "无修复", "链上代币聚集 → 历史 APK 逆向重建"),
]


def log10_binom_tail(n, k, p):
    """P(X >= k)，用对数算，否则会直接下溢到 0。"""
    total = -math.inf
    for i in range(k, n + 1):
        lg = (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
              + i * math.log(p) + (n - i) * math.log1p(-p))
        total = lg if total == -math.inf else max(total, lg) + math.log1p(
            math.exp(min(total, lg) - max(total, lg)))
    return total / math.log(10)


def main():
    banner(12, "从链上反推到是哪个软件",
           "枚举出一份弱钥匙名单，只做完了一半。另一半是：**搞清楚这是哪个软件做的** —— "
           "因为不知道是哪个软件，就没有任何人可以被通知。",
           "Coinspect《Identifying the Wallets Behind Vulnerable Recovery Phrases》"
           "illbloom.org/articles/identifying-wallets-vulnerable-recovery-phrases/（本课已读原文）")

    section("1 · 为什么这一步必须做")
    print("""  第 5 课那个「未知软件」案例是整个案例库里最坏的形态：
  13.7 万枚 BTC 的量级，而**造出这些钥匙的软件至今没人知道是哪个**。

  后果不是「少一条知识」，是：
    · 没有东西可以打补丁
    · **没有任何人可以被通知「你用过那个工具，赶紧换钱包」**
    · 它可能还在生成新的弱钱包

  一条公开的链上地址，**不会告诉你它是哪个应用生成的**。
  如果那个应用是闭源的、而且已经停运，生成它的那个版本可能已经不存在于世上了。""")

    section("2 · Coinspect 实际走通的五条路（没有一条是通用方法）")
    print("  " + pad("应用", 22) + pad("状态", 10) + pad("修复", 24) + "怎么认出来的")
    print("  " + "-" * 96)
    for name, status, fix, how in CONFIRMED:
        print("  " + pad(name, 22) + pad(status, 10) + pad(fix, 24) + how)
    print("""
  值得注意的是**入口的多样性**：一个是厂商自己被盗之后找上门（反向入口），
  一个靠公开源码，一个靠 npm 依赖链，一个靠开发者的 Twitter，
  一个靠**链上代币的聚集**。

  Coinspect 自己的话：「没有单一路径。」
  → 这说明防守侧的这一步**没法自动化**，它是人力密集的。
    第 13 课那个「防守方人力极少」的混淆因素，具体就长这样。""")

    section("3 · 可跑：「代币聚集」这个信号到底有多强")
    print("""  Milo 那条线最漂亮：在 256 位搜索的某个子集里，
  **96% 的钱包都收到过同一个代币**（Polygon 上的 Milo）。

  这为什么是个线索而不是巧合？算一下。""")
    n, hits = 500, 480                    # 500 个地址，96% = 480 个
    baseline = 0.0002                     # 假设该代币在普通地址里的持有率 0.02%
    lg = log10_binom_tail(n, hits, baseline)
    print(f"\n  子集大小                     {n} 个地址")
    print(f"  其中持有该代币               {hits} 个（{hits / n:.0%}）")
    print(f"  假设普通地址的持有率         {baseline:.2%}")
    print(f"  纯属巧合的概率               10^{lg:.0f}")
    print(f"\n  （基线 {baseline:.2%} 是我设的一个保守假设；"
          f"把它放大 100 倍到 2%，结论也不变 —— 自己改 baseline 跑一遍。）")
    for b in (0.002, 0.02, 0.10):
        print(f"      baseline = {b:>5.1%}  →  10^{log10_binom_tail(n, hits, b):.0f}")
    print("""
  → **这就是「归因」的全部机理：弱钥匙是同源的，所以它们的链上行为也同源。**
    生成器把一群人绑在了一起，而那个绑定在链上是看得见的。

  顺带一个让人不舒服的推论：**这个方法攻击者同样能用。**
  它不是防守方的独门武器，它只是防守方碰巧也会用。""")

    section("4 · 可跑：依赖存在 ≠ 被用于生成钱包")
    print("""  Coinspect 有一句方法论警句，值得当成这一课的标题：

      **「知道一个项目依赖了含缺陷实现的库，只是起点。」**

  因为同一个库可能被用在很多地方，而且多数地方和密钥无关。
  必须**追进去**，确认它真的在钱包生成路径上。

  下面两个文件依赖**完全相同**的缺陷库。只有一个是真受影响的：""")
    auditor = os.path.join(HERE, "..", "14_prediction", "audit_wallet_code.py")
    rows = []
    for f in ("uses_it_for_keys.js", "uses_it_for_ui.js"):
        fp = os.path.join(HERE, "samples", f)
        r = subprocess.run([sys.executable, auditor, fp], capture_output=True, text=True)
        flagged = r.stdout.count("🔴") + r.stdout.count("🟠") + r.stdout.count("🟡")
        txt = open(fp, encoding="utf-8").read()
        # 追调用链：缺陷函数出现在 createWallet 的函数体里吗
        body = txt.split("function createWallet")[1].split("}")[0] if \
            "function createWallet" in txt else ""
        in_wallet = "WordArray.random" in body
        rows.append((f, flagged, in_wallet))
    print("\n  " + pad("文件", 26) + pad("嗅探器命中", 14) + "缺陷函数在 createWallet 体内？")
    print("  " + "-" * 72)
    for f, flagged, in_wallet in rows:
        print("  " + pad(f, 26) + pad(f"{flagged} 条", 14)
              + ("是 ← 真受影响" if in_wallet else "否 ← 依赖在，但没用来造钥匙"))
    same = len({r[1] for r in rows}) == 1
    print(f"\n  两个文件的命中数一样吗: {same}"
          f"  ← 自动化**分不开**它们")
    print("  能分开它们的只有最后一列，而最后一列要读调用链。")
    print("""
  这就是为什么第 14 课那个嗅探器的结尾写着「规则命中不等于有漏洞」。
  **自动化能给你候选名单，不能给你结论。** 结论要人读调用链。""")

    section("5 · 配置维度：每认出一个钱包，搜索空间就变大一次")
    print("""  Coinspect 原话（本课已读原文）：

  > 一旦确认了一个钱包，我们还必须确定它支持哪些配置。
  > 不同的助记词语言、熵长度和派生路径，会在不同网络上导出不同的钱包和地址集合。
  > **这些配置不可互换：每一个都可能需要一次独立的搜索，
  > 同时扩大地址空间和所需的计算量。**

  所以这项调查是**迭代**的：
      链上分析 → 找到一个钱包 → 这个钱包带出新的生成参数
      → 新参数导出新地址 → 新地址可能又指向新的应用 → 回到第一步

  这条对第 8 课那个成本公式有直接影响，去看那一课的「配置维度」一节。""")

    section("6 · 这一课的红线")
    print("""  本课程只讲**已经被公开披露、并且已经被修复或已停止维护**的案例，
  而且只引用厂商或研究机构**自己公开过**的归因结论。

  **不会出现在这个公开仓库里的东西：**
    ✗ 任何「可疑钱包清单」或未经确认的候选应用
    ✗ 任何尚在调查中的生态的目标名单

  理由很简单：那种清单**既是一份未经证实的指控，也是一张给攻击者的地图**。
  归因的价值在于通知受影响的用户，不在于点名。

  Coinspect 自己也把这条写在了结论里：他们列出的五个
  「只是目前已确认的，不是完整名单」。**不完整是诚实，不是缺陷。**""")


if __name__ == "__main__":
    main()
