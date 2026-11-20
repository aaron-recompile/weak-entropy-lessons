# 弱熵的统一规律

> 十三年，十一个独立案例，十一个不同的团队，**没有一次把密码学写错**。
> 每一次都是在操作系统的随机数接口外面包了一层。
>
> 而攻击者不是在猜你的钥匙 —— 他是在**重新运行当年生成你钥匙的那段代码**。

一门可以自己跑的课。每一课配一段**真的能跑出结果**的最小代码 —— 不是伪代码，
是跑完就看见弱钥匙被算出来的那种。

**📖 连载 HTML 版：https://bitcoincoding.dev/weak-entropy-lessons/**

---

## 为什么是「第 1 道门」

私钥安全不是一件事，是三道门串在一起：**①造钥匙 ②存钥匙 ③用钥匙**。

全世界讨论的是门 2 和门 3。钱主要是从门 1 丢的 —— 因为**只有门 1 的失败是静默的**。
门 2 失败你知道（东西丢了），门 3 失败你看得见（屏幕上地址不对），
门 1 失败什么都看不出来，直到某一天余额是 0。

---

## 跑起来

只用 Python 标准库，没有任何依赖。椭圆曲线、BIP39、BIP32、MT19937 全部在仓库里从头实现 ——
因为这门课的要点就是**不要相信包装层**，包括我写的那些。

```sh
git clone https://github.com/aaron-recompile/weak-entropy-lessons.git
cd weak-entropy-lessons
./run_all.sh -q            # 十四课全部跑一遍，约 45 秒
python3 lessons/01_recompute/recompute.py
```

第 8 课另外需要一个 C 编译器和 make（macOS / Linux 自带）：

```sh
cd lessons/08_coldcard_link && make all
```

---

## 十四课

| # | 课 | 案例 | 跑什么 |
|---|---|---|---|
| 01 | [不是碰撞，是重算](lessons/01_recompute/) | — | **后面十三课的第一性原理**：算出碰撞概率，再看同一个生成器两次跑出字节级相同的钥匙 |
| 02 | [强随机数没有「第一个钱包」](lessons/02_milk_sad/) | bx seed / Milk Sad，CVE-2023-39910 | 逐字复现 `milk sad wage cup…`，然后几秒内反推出一把钥匙 |
| 03 | [一个坏掉的随机数，活了十二年](lessons/03_ill_bloom/) | CryptoJS / Ill Bloom，CVE-2026-71851 | 复现 `illness blossom…`，Python 与原版 JS 逐字节对照 |
| 04 | [2³² 到底有多小](lessons/04_trust_wallet_wasm/) | Trust Wallet 扩展，CVE-2023-31290 | 建一张迷你彩虹表，微秒级查表还原种子 |
| 05 | [不安全的那个是默认值](lessons/05_cake_wallet/) | Cake Wallet | **把整个 2²⁰ 空间走完**（约 2 秒） |
| 06 | [同一段代码，三个弱钱包范围](lessons/06_php_mt_rand/) | PHPCoinAddress | MT_RAND_PHP 对 MT_RAND_MT19937，数出一半输出不同 |
| 07 | [人选的口令](lessons/07_brainwallet/) | 脑钱包 | 从地址反推口令，顺便看曲线乘法有多贵 |
| 08 | [这次失败，恰恰来自那个冲突的缺席](lessons/08_coldcard_link/) | **Coldcard** | **C + Makefile 复现链接期符号绑错**，去掉 `static` → 构建直接失败 |
| 09 | [XOR 不生产随机性](lessons/09_xor/) | — | 穷举三种情形，数出 XOR 之后的真实空间 |
| 10 | [PBKDF2 救不了你](lessons/10_pbkdf2/) | — | 在本机量出那个常数值几位熵（答案：十位以内） |
| 11 | [五道保险，五道都没响](lessons/11_five_guards/) | Coldcard | 四个真的统计检验，对弱 PRNG **全部通过** |
| 12 | [从链上反推到是哪个软件](lessons/12_attribution/) | Ill Bloom 的五个应用 | 算出「96% 持有同一代币」这个信号有多强；看嗅探器分不开两个依赖相同的文件 |
| 13 | [攻击者的节奏](lessons/13_attacker_tempo/) | 全部 | 量出攻防不对称；**为什么攻击者要等三到六年** |
| 14 | [一个可证伪的赌注](lessons/14_prediction/) | — | 包装层嗅探器 + 一个你自己能跑的取样实验 |

---

## 这门课的三条规矩

1. **大白话在前，细节在后。** 每课开头那段几乎不含数字。只想拿一个心智模型就走，看它就够了。
2. **每个数字都能指回出处，而且带证据分级**（很强 / 强 / 中 / 弱）。
   标「弱」的不要单独使用 —— 哪怕它是流传最广的那个。
3. **能跑的就不要只是读。**

### 几个被广泛引用、但本课程认为撑不住的数字

| 数字 | 为什么不用 |
|---|---|
| Randstorm 的「140 万 BTC」 | 全部二手；口径是**暴露量估计**而非实测弱钥匙；来源是一家商业找回公司 |
| Coldcard 的损失金额 | 二手口径从 $7,500 万漂到 $1.3 亿；Coinkite 官方不给总额。**机理和搜索空间是硬的，金额不是** |

---

## 结构

```
lessons/
  common/          MT19937、BIP39、BIP32 + secp256k1、工具 —— 全部从头实现，带官方测试向量自检
  01_milk_sad/ … 12_prediction/
  07_coldcard_link/   C + Makefile + nm 校验脚本（本课最值钱）
docs/              连载 HTML（GitHub Pages）+ 五张机理动图（SVG）
site/              生成 docs/ 的脚本
run_all.sh         把十二课全部跑一遍
```

---

## 出处

全部来自公开材料，没有使用任何非公开信息：

- **Milk Sad** 研究更新 #1–#22 — `milksad.info`（Christian Reitter 等）
- **Wizardsardine** Coldcard 逐 commit 解剖，2026-08-11（Loïc Morel）
- **Coinkite** 官方公告，2026-07-30
- **Ledger Donjon** Trust Wallet 扩展复盘，2023-04-25
- **Coinspect** — `illbloom.org`（含归因文和中文助记词盗转分析，本课程已读原文）、`unlukey.org`
- CVE-2023-39910 / CVE-2023-31290 / CVE-2024-23660 / CVE-2026-71851

## 这门课从哪来

它是一份更大的、不公开的比特币长期风险研究里「托管与实现攻击面」那一章的
**第 1 道门**部分，做成了可以动手跑的形式。源文档（私有笔记，不在本仓库）：

- `03a_弱熵案例库.md` — 605 行，十一个案例逐案拆解，每个数字带证据分级
- `03_托管与实现攻击面.md` — 三道门的完整框架

**本仓库只包含可公开的技术部分。** 源文档里的投资判断没有、也不会进入这里。

---

## ⚠️ 免责

见 [DISCLAIMER.md](DISCLAIMER.md)。一句话：这里复现的全部是**已被公开披露并已修复**的历史缺陷，
用固定 demo 种子，不联网，不碰任何真实密钥。

如果你怀疑自己的钱包受影响：**不要用这个仓库去验证。**
去看对应厂商的官方公告，按它的指引操作。
