#!/usr/bin/env python3
"""
第 8 课（配套）· 把 Coldcard Mk3 那 2^22 个起始状态当成一个空间来看。

    python3 enumerate_mk3.py
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from lesson import banner, section, fmt_dt, pad                   # noqa: E402

# Wizardsardine 枚举出来的结果（一手，逐 commit 的分析文）
MK3_STATES = 4_456_448                    # = 2^22.09
UID_POSITIONS = 3_300                     # 晶圆上大约这么多个可达位置（他们的模型）
GPU_PER_SEC = 1_500_000                   # 单张 RTX 4090 实测，含 BIP32 派生 + 地址查表
GPU_RENT_HOUR = 0.30                      # 美元


def yasmarang_stream(seed, n=8):
    """和 micropython_rng.c 里那段同构，用来演示「一个 32 位种子 → 一条确定的流」。"""
    pad, nn, d, dat = seed & 0xFFFFFFFF, 0, 0, 0
    out = []
    for _ in range(n):
        pad = (pad + dat + d * nn) & 0xFFFFFFFF
        pad = ((pad << 3) | (pad >> 29)) & 0xFFFFFFFF
        nn = pad | 2
        d ^= ((pad << 31) + (pad >> 1)) & 0xFFFFFFFF
        d &= 0xFFFFFFFF
        dat ^= (pad & 0xFF) ^ ((d >> 8) & 0xFF) ^ 1
        out.append((pad ^ ((d << 5) & 0xFFFFFFFF) ^ (pad >> 18) ^ (dat << 1)) & 0xFFFFFFFF)
    return out


def main():
    banner(8, "Coldcard —— 链接期的符号绑定（2021-03 → 2026-07）",
           "史上最大的硬件钱包损失，不是因为设备被攻破。设备好得很。"
           "是因为一个编译开关，让它五年多没接上自己的硬件随机数芯片。",
           "Coinkite 公告 2026-07-30；Wizardsardine 逐 commit 解剖 2026-08-11，"
           "wizardsardine.com/blog/coldcard-vuln-deep-dive/")

    print("""  ⚠️  本课的全部 Coldcard 材料都来自上面这两个公开出处。
      可跑的实验在同目录的 C 代码里：

          make all        （broken → duplicate → archive → fixed → verify）

      本脚本只做一件事：把那个搜索空间的大小摸出来。""")

    section("1 · 种子的两个输入，XOR 进同一个 32 位字里（所以不叠加）")
    print("""  ① **芯片唯一标识符的 32 位** —— 这些位编码的是晶片在晶圆上的坐标。
       按 Wizardsardine 的模型最多 14 位携带信息，其中 12 位可达
       → Mk3 上大约 3,300 个位置。**这个值既不变，也不保密。**

  ② **SysTick** —— 一个每毫秒回绕一次的计数器。

  Mk2/Mk3 上另一个本该贡献 24.4 位的 RTC，**价值为零**
  —— 它指向一个固件从来没启动过的振荡器。
  于是 Mk2/Mk3 上剩下的唯一变量，是**第一次按键的时刻**，上限 16.3 位。""")

    section("2 · 一个 32 位种子，一条确定的流")
    demo = [(0x0041002A, 1234), (0x0041002A, 1235), (0x0041002B, 1235)]
    for uid, tick in demo:
        seed = uid ^ tick
        print(f"  UID=0x{uid:08X} SysTick={tick:<5} → 种子 0x{seed:08X} → "
              f"{[hex(x) for x in yasmarang_stream(seed, 3)]}")
    print("\n  每个种子一条流 —— 但**流的条数是有限的，而且很少**。")
    print("""
  顺手看一个「XOR 进同一个字里（所以不叠加）」的直接后果：""")
    a, b = (0x0041002A, 1235), (0x0041002B, 1234)
    print(f"      UID=0x{a[0]:08X} SysTick={a[1]} → 种子 0x{a[0] ^ a[1]:08X}")
    print(f"      UID=0x{b[0]:08X} SysTick={b[1]} → 种子 0x{b[0] ^ b[1]:08X}")
    print(f"      两台不同的芯片、不同的时刻，种子一样吗: {(a[0] ^ a[1]) == (b[0] ^ b[1])}")
    print("""
  **两个输入 XOR 进同一个 32 位字，所以它们不是相加的 —— 它们会互相抵消。**
  这是第 9 课的预告：XOR 不生产随机性。""")

    section("3 · 那个空间有多大")
    print(f"  Wizardsardine 枚举的结果：**{MK3_STATES:,} 个起始状态 = 2^{math.log2(MK3_STATES):.2f}**")
    print(f"  （分解成 4096 × 1088 能复出这个总数；具体分解是他们的建模，不是实测事实。）")
    t0 = time.perf_counter()
    n = 60_000
    for s in range(n):
        yasmarang_stream(s, 1)
    rate = n / (time.perf_counter() - t0)
    print(f"\n  本机速率（纯 Python，只算 PRNG 第一个字）：{rate:,.0f} 个/秒")
    print(f"  走完 {MK3_STATES:,} 个：本机 {fmt_dt(MK3_STATES / rate)}")
    print(f"  Wizardsardine 实测单张 RTX 4090（含 BIP32 派生 + 地址查表）：")
    print(f"      {fmt_dt(MK3_STATES / GPU_PER_SEC)}，租用成本 "
          f"${MK3_STATES / GPU_PER_SEC / 3600 * GPU_RENT_HOUR:.6f}")
    print("\n  **3 秒。成本可忽略。这是 Mk3。**")

    section("4 · Mk3 和 Mk4/Mk5/Q 之间是「种类」的差别，不是「程度」的差别")
    rows = [("2^22  Mk3，抽取序号已知", 2 ** 22),
            ("2^28", 2 ** 28),
            ("2^32.05  同一台 Mk3，序号假设在 0–1000", int(2 ** 32.05)),
            ("2^40", 2 ** 40),
            ("2^46  Mk4，完整标识符已知", 2 ** 46),
            ("2^52  Mk4 的建模切片", 2 ** 52),
            ("2^60", 2 ** 60)]
    print("  " + pad("搜索空间", 40) + pad("单张 4090", 16, ">") + pad("租用成本", 18, ">"))
    print("  " + "-" * 74)
    for name, size in rows:
        sec = size / GPU_PER_SEC
        cost = sec / 3600 * GPU_RENT_HOUR
        if cost < 0.005:
            cs = "可忽略"
        elif cost < 1e4:
            cs = f"${cost:,.2f}"
        else:
            cs = f"${cost:,.0f}"
        print("  " + pad(name, 40) + pad(fmt_dt(sec), 16, ">") + pad(cs, 18, ">"))
    print(f"""
  **3 秒 vs 约 74 年。这 29.5 位的差距完全来自安全元件那 32 位的 reseed。**
  Wizardsardine 的原话：**它是这整条链里唯一一个真正起了作用的机制。**

  → 门 2（设备硬件）确实救了现代机型。
    门 2 不是没用 —— 它是在门 1 塌了之后，唯一还在承重的东西。""")

    section("4b · 成本公式还缺一项：配置维度")
    print("""  前面那张表算的是**生成器的状态空间**。真实的扫荡成本还要再乘一项：

        成本 = |生成器状态空间| × |配置数|

  Coinspect 的原话（《Identifying the Wallets Behind Vulnerable Recovery Phrases》）：

  > 不同的助记词语言、熵长度和派生路径，会在不同网络上导出不同的钱包和地址集合。
  > **这些配置不可互换：每一个都可能需要一次独立的搜索，
  > 同时扩大地址空间和所需的计算量。**

  配置数怎么来的，自己数一遍（别信这个数，数给你看）：""")
    langs, sizes, paths = 10, 5, 15
    cfg = langs * sizes * paths
    print(f"      BIP39 官方词表语言数        {langs}")
    print(f"    × 熵长度（128/160/192/224/256）{sizes}")
    print(f"    × 常见派生路径模板            约 {paths}")
    print(f"    = **约 {cfg} ≈ 2^{math.log2(cfg):.1f}**")
    print(f"\n  代进去：")
    for name, st in (("Mk3", 2 ** 22), ("Mk4/Mk5/Q 的建模切片", 2 ** 52)):
        tot = st * cfg
        print(f"      {name:<24} 2^{math.log2(st):.0f} × {cfg} ≈ "
              f"**2^{math.log2(tot):.0f}**  （单张 4090 {fmt_dt(tot / GPU_PER_SEC)}）")
    print("""
  **2^32 不算什么；2^62 是死路。** 这两句话比裸的 2^22 / 2^52 更接近真实的攻击经济。

  ⚠️  但这一项要用对，它有两个方向：

    · **扫荡者**（不知道受害者用的是哪个配置）付的是上面这个乘积。
    · **定点攻击者**（已经知道型号、固件、语言、派生路径）**不付这一项** ——
      他付的就是裸的状态空间。Wizardsardine 那个「Mk3 三秒」就是这种情形。

  所以配置维度**保护不了你**。它只是解释了为什么研究者的全量枚举那么慢、
  为什么攻击者是「随时间逐步」抽干而不是一次扫完（第 13 课那个反应窗口）。

  （证据说明：那段引文和「配置不可互换」这个原则是 Coinspect 一手的，
   针对的是钱包应用的调查；把它代到 Coldcard 的数字上是**我做的演算**，
   不是 Coinspect 对 Coldcard 的结论。配置数 {cfg} 也是我数出来的量级估计。）""".replace("{cfg}", str(cfg)))

    section("5 · 一个让人很不舒服的推论：两台不同的设备可能生成同一个种子")
    print("""  既然种子的主要输入是晶圆坐标（不变、不保密），那就会碰撞。
  这不是「两个人密码一样」那种巧合，是**制造工艺决定的**。
  论文里的原话甚至说：「晶圆的几何形状在输出里透出来了。」""")
    # 生日问题：n ≈ 1.1774 * sqrt(K) 时碰撞概率 1/2
    n_half = 1.1774 * math.sqrt(UID_POSITIONS)
    print(f"\n  按「约 {UID_POSITIONS:,} 个可达位置」算，生日问题给出 1/2 碰撞概率的台数：")
    print(f"      n ≈ 1.1774 × √{UID_POSITIONS:,} = {n_half:.0f} 台")
    print(f"  Wizardsardine 给的是 **68 台**。对得上（反解回去：(68/1.1774)² ≈ "
          f"{(68 / 1.1774) ** 2:,.0f} 个位置）。")
    print("\n  那「约 120 对共享同一个起始状态」是怎么来的 —— 以及它有多软：")
    for units in (30_000, 33_000, 40_000):
        pairs = units * (units - 1) / 2 / MK3_STATES
        print(f"      假设保有量 {units:,} 台 → 期望 {pairs:,.0f} 对")
    print("""
  原文给的是「约 120 对」，对应 3.3 万台左右。

  ⚠️  **保有量是一个假设值。Wizardsardine 自己说「Coinkite 之外没人能核」。**
      所以这条该这么用：机理是确定的（碰撞必然存在），
      **具体对数是一个对假设高度敏感的估计，不要当事实引用。**
      ——这也是整个课程对待数字的方式：阈值只在产生它的约束条件下有效。""")

    section("6 · 哪些东西没坏")
    print("""  Wizardsardine 列的「没坏的」清单，每一条都有信息量：

      ECDSA nonce      走 RFC 6979，**确定性的，根本不用随机数**
      备份加密         不走这条路径
      **纯骰子路径**   见下

  → 注意第一条。**整个行业解决 nonce 问题的办法，是把随机数从那一步彻底移除。**
    而造种子那一步**没法**确定性化 —— 它是唯一一个必须真的有随机性的地方。
    这就是为什么第 1 道门比别的门更危险。

  受影响的则包括：纸钱包私钥（**生成器的原始输出，不走 PBKDF2，所以更便宜**）、
  克隆、Key Teleport、USB 会话密钥、侧信道掩码。
  **BIP-85 是确定性派生的，所以它恰好等于父种子的价值** —— 父种子弱，所有子钱包一起弱。""")

    section("7 · 骰子为什么救了人")
    print("""  **在这次事故里，唯一完全没有风险的用户，是那些不相信设备随机数、自己掷了骰子的人。**

  Coinkite 的官方阈值：
      50 到 98 次独立、私密、公平的掷骰  → 骰子**单独**就贡献至少 128 位熵
      99 次以上                          → 约 256 位
      少于 50 次，或者记不清            → 必须迁移

  机理（Wizardsardine 在模拟器上逐函数插桩验证过）：
  纯骰子路径上，SHA-256 累加器**从空字符串开始**，只吃掷骰结果。
  种子恰好等于 BIP39(sha256(掷骰字符串))。

  他验证的办法很漂亮：跑 100 次掷骰的 trace，开头的摘要是 e3b0c442...b7852b855
  —— **空字符串的标准哈希值**，证明第一次掷骰之前累加器里什么都没有。
  设备的熵根本没进来，所以 bug 碰不到它。""")
    import hashlib
    print(f"\n  自己验一下那个摘要：sha256(b'') = {hashlib.sha256(b'').hexdigest()}")
    print("""
  **但混合模式有两个坑：**
    1. 「拒绝某一面占比超过 30%」的分布检查在 seed.py:452，
       **只在 judge_them 参数为真时才生效**。
    2. 从词表界面按 `4` 进入的混合模式，调用的是 add_dice_rolls(0, seed, False)
       —— **同时关掉了那个分布检查和最少次数要求。**

  → 「我掷了骰子」这句话本身不够。**得知道是从哪个入口掷的。**""")

    section("8 · 受影响的固件区间（Coinkite 官方）")
    print("""      Mk2 / Mk3     4.0.1（2021-03）到 4.1.9 含
      Mk4 / Mk5     5.6.0 之前
      Q             1.5.0Q 之前
      Edge 轨道     6.6.0X / 6.6.0QX

  ⚠️  Coinkite 特别警告：**Edge 和标准是两条独立发布轨。
      不要因为 Edge 的 6.x 版本号数字更大就以为它修了。**

  1,962 天 —— 从第一个脆弱发布版（4.0.0，2021-03-17）到修复（2026-07-31）。
  （有的二手来源写 1,978 天，那是从 2021-03-01 起算的。机理不受影响。）""")


if __name__ == "__main__":
    main()
