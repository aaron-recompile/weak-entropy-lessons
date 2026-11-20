#!/usr/bin/env python3
"""
第 14 课（工具）· 包装层嗅探器。

把十一个历史案例的共同形状写成规则，用来扫一段「生成助记词/私钥」的代码。

    python3 audit_wallet_code.py samples/*.js samples/*.py samples/*.c
    python3 audit_wallet_code.py 你自己的文件
    cat 某段代码 | python3 audit_wallet_code.py -

这不是一个通用的安全扫描器，它只回答一个问题：
**这段代码在操作系统的随机数接口外面包了一层吗？**
"""
import re
import sys

# 规则格式：(编号, 正则, 严重度, 名字, 它对应哪个历史案例)
RULES = [
    ("R1", r"\bMath\.random\s*\(", "致命", "用了 Math.random()",
     "CryptoJS / Ill Bloom（2^39）"),
    ("R1", r"WordArray\.random\s*\(", "致命", "用了 CryptoJS 的 WordArray.random()",
     "CryptoJS / Ill Bloom（CVE-2026-71851，4.0.0 前）"),
    ("R1", r"\bstd::mt19937(_64)?\b|\bmt19937\b|\bMersenneTwister\b", "致命",
     "用了 Mersenne Twister", "bx seed（2^32）、Trust Wallet 扩展（2^32）"),
    ("R1", r"\bmt_rand\s*\(|\brand\s*\(\s*\)|\bsrand\s*\(", "致命",
     "用了 rand/srand/mt_rand", "PHPCoinAddress（7,713.5 BTC）"),
    ("R1", r"(?<!Secure)\bRandom\s*\(\s*\)(?!\s*=>)", "高",
     "用了语言自带的非密码学 Random()", "Cake Wallet（20 位）"),
    ("R1", r"\brandom\.(random|randint|randrange|getrandbits|choice)\s*\(", "致命",
     "用了 Python 的 random 模块（是 MT19937）", "同 bx seed"),

    ("R2", r"\btime\s*\(\s*(NULL|0|nullptr)\s*\)|\bDate\.now\s*\(|"
           r"\btime\.time\s*\(|GetCurrentTimeMicros|\bSystem\.currentTimeMillis",
     "致命", "用时间做种子", "Trust Wallet iOS（31 位）、Cake Wallet（20 位）"),

    ("R3", r"def\s+\w*random\w*\([^)]*\bsecure\s*=\s*False|"
           r"\bbool\s+secure\s*=\s*false|\{\s*bool\s+secure\s*=\s*false\s*\}",
     "致命", "随机数包装层的安全开关默认是不安全的那一侧", "Cake Wallet（修复只有 14 个字符）"),

    ("R4", r"(getRandomValues|urandom|getrandom|randombytes|RNGCryptoServiceProvider)"
           r"[\s\S]{0,120}?(\|\||catch|except|fallback|else)",
     "高", "在 CSPRNG 外面套了 fallback / try-except", "BitcoinJS SecureRandom（Randstorm）"),

    ("R5", r"\^[\s\S]{0,40}?(prng|rand|rng)\w*\s*\(", "中",
     "把随机源 XOR 在一起 —— 问一句：有哪个操作数是强的？", "Coldcard（两个软件 PRNG 相 XOR）"),

    ("R6", r"\bextern\s+\w[\w\s\*]*\brng\w*\s*\(|\bextern\s+\w[\w\s\*]*\brandom\w*\s*\(",
     "高", "随机数函数靠链接期解析外部符号", "Coldcard（1,962 天，2^22）"),

    ("R7", r"(except|catch)[\s\S]{0,60}?(pass\b|return\s+(0|null|nil|None)|\{\s*\})",
     "高", "吞掉了异常 —— 随机数失败必须是致命错误", "Coinspect 的第二条建议"),
]

GOOD = [
    (r"\bos\.urandom\s*\(", "os.urandom()"),
    (r"\bsecrets\.(token_bytes|randbits)\s*\(", "secrets 模块"),
    (r"crypto\.getRandomValues\s*\(", "crypto.getRandomValues()"),
    (r"crypto\.randomBytes\s*\(", "crypto.randomBytes()"),
    (r"\bgetrandom\s*\(", "getrandom(2)"),
    (r"\bRandom\.secure\s*\(", "Dart 的 Random.secure()"),
    (r"SystemRandom\s*\(", "SystemRandom"),
]

SEVERITY_ORDER = {"致命": 0, "高": 1, "中": 2}


def strip_comments(text):
    """把注释内容抹掉但保留行数 —— 否则注释里提到 Math.random() 也会误报。"""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"/\*[\s\S]*?\*/", blank, text)
    text = re.sub(r"(?m)//.*$", blank, text)
    text = re.sub(r"(?m)(?<!['\"])#.*$", blank, text)
    return text


def audit(text, name):
    lines = text.splitlines()
    text = strip_comments(text)
    hits = []
    for rid, pat, sev, what, case in RULES:
        for m in re.finditer(pat, text, re.IGNORECASE if rid == "R3" else 0):
            ln = text[:m.start()].count("\n") + 1
            hits.append((sev, rid, ln, what, case, lines[ln - 1].strip()[:72]))
    seen = set()
    uniq = []
    for h in sorted(hits, key=lambda h: (SEVERITY_ORDER[h[0]], h[2])):
        key = (h[1], h[2])
        if key not in seen:
            seen.add(key)
            uniq.append(h)
    good = [label for pat, label in GOOD if re.search(pat, text)]
    return uniq, good


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    files = []
    for a in args:
        if a == "-":
            files.append(("<stdin>", sys.stdin.read()))
        else:
            try:
                files.append((a, open(a, encoding="utf-8", errors="replace").read()))
            except OSError as e:
                print(f"读不了 {a}: {e}")
    worst = 0
    for name, text in files:
        hits, good = audit(text, name)
        print(f"\n{'═' * 74}\n{name}\n{'═' * 74}")
        if good:
            print(f"  ✅ 用到了密码学安全的随机源：{', '.join(good)}")
        if not hits:
            print("  ✅ 没有命中任何「包装层」规则。")
            continue
        for sev, rid, ln, what, case, src in hits:
            mark = {"致命": "🔴", "高": "🟠", "中": "🟡"}[sev]
            print(f"  {mark} [{rid} {sev}] 第 {ln} 行 · {what}")
            print(f"       {src}")
            print(f"       历史对应：{case}")
            worst = max(worst, 1 if sev == "中" else 2)
        if good:
            print("\n  ⚠️  同时出现「安全的随机源」和「包装层」通常意味着有 fallback —— "
                  "这正是 Randstorm 的形状。")
    print(f"\n{'─' * 74}")
    print("提醒：规则命中不等于有漏洞，没命中也不等于安全。")
    print("这个工具只替你把「有没有包装层」这个问题问出来 —— 答案还是要你读代码。")
    return worst


if __name__ == "__main__":
    sys.exit(main())
