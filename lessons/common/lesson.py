"""每课共用的小工具：路径、横幅、免责声明、计时。"""
import os
import sys
import time

COMMON = os.path.dirname(os.path.abspath(__file__))
if COMMON not in sys.path:
    sys.path.insert(0, COMMON)

DISCLAIMER = (
    "本实验复现的是**已被公开披露并已修复**的历史缺陷，用于教学。\n"
    "  全部使用固定的 demo 种子，不生成任何真实钱包，不联网，不查询任何人的地址。"
)


def banner(num, title, one_liner, source):
    bar = "─" * 72
    print(f"\n{bar}\n第 {num} 课 · {title}\n{bar}")
    print(f"\n【大白话】{one_liner}\n")
    print(f"⚠️  {DISCLAIMER}")
    print(f"\n出处：{source}\n{bar}")


def dwidth(s):
    """终端显示宽度：CJK 和全角符号算 2 列。对齐表格要用这个，不能用 len()。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, w, align="<"):
    fill = max(0, w - dwidth(s))
    return (" " * fill + s) if align == ">" else (s + " " * fill)


def section(t):
    print(f"\n── {t} " + "─" * max(4, 72 - dwidth(t) - 4))


class timer:
    def __enter__(self):
        self.t = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.dt = time.perf_counter() - self.t

    @property
    def elapsed(self):
        return time.perf_counter() - self.t


def human(n):
    """2^22 这种数字写成人能读的样子。"""
    import math
    if n <= 0:
        return str(n)
    return f"{n:,} = 2^{math.log2(n):.2f}"


def rate_table(per_sec, spaces, label="本机 Python"):
    """给定实测速率，把几个搜索空间的耗时列出来 —— 诚实地标是哪台机器。"""
    import math
    print(f"  实测速率（{label}）：{per_sec:,.0f} 候选/秒")
    print("  " + pad("搜索空间", 30) + pad("本机耗时", 20, ">") + pad("单张 RTX 4090", 20, ">"))
    print("  " + "-" * 70)
    GPU = 1_500_000      # Wizardsardine 实测：约 150 万完整候选/秒（含 BIP32 派生 + 地址查表）
    for name, size in spaces:
        print("  " + pad(name, 30) + pad(fmt_dt(size / per_sec), 20, ">")
              + pad(fmt_dt(size / GPU), 20, ">"))
    print("\n  GPU 那一列的 150 万/秒来自 Wizardsardine 的实测（单张 4090，租用 $0.30/小时）。")


def fmt_dt(sec):
    if sec < 1:
        return f"{sec * 1000:.0f} 毫秒"
    if sec < 90:
        return f"{sec:.1f} 秒"
    if sec < 5400:
        return f"{sec / 60:.1f} 分钟"
    if sec < 86400 * 2:
        return f"{sec / 3600:.1f} 小时"
    if sec < 86400 * 730:
        return f"{sec / 86400:.1f} 天"
    years = sec / 86400 / 365.25
    if years < 1e6:
        return f"{years:,.0f} 年"
    return f"{years:.1e} 年"


UNIVERSE_YEARS = 1.38e10


def vs_universe(sec):
    """大到没有意义的时间，换成「宇宙年龄的多少倍」才有画面。"""
    y = sec / 86400 / 365.25
    if y < UNIVERSE_YEARS:
        return fmt_dt(sec)
    return f"宇宙年龄的 {y / UNIVERSE_YEARS:.1e} 倍"
