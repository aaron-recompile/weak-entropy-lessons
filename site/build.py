#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 docs/ 下的连载 HTML（GitHub Pages）和 artifact/ 下的手机版。

    python3 site/build.py
"""
import html
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
ART = os.path.join(ROOT, "artifact")
sys.path.insert(0, HERE)
from content import COURSE, SUBTITLE, REPO, INTRO_PLAIN, LESSONS  # noqa: E402

CSS = """
/* 版面：单栏阅读流，顶部固定导航；大白话卡片用左侧强调线和更大的字号把它顶到最前面 */
:root{
  --bg:#f7f6f3; --surface:#fff; --surface-2:#f0eee9;
  --ink:#1b1a19; --muted:#6f6a63; --rule:#e2ded6;
  --accent:#2d5d7c; --weak:#a32d2f; --sound:#1f6f4a; --warnbg:#fdf6ec;
  --display:"Space Grotesk","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --body:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --bg:#131316; --surface:#1c1c21; --surface-2:#232329;
  --ink:#e8e6e3; --muted:#9a958e; --rule:#2e2e36;
  --accent:#7fb3d5; --weak:#ff8f8a; --sound:#6fd9a4; --warnbg:#262017;
  color-scheme:dark; } }
:root[data-theme="dark"]{
  --bg:#131316; --surface:#1c1c21; --surface-2:#232329;
  --ink:#e8e6e3; --muted:#9a958e; --rule:#2e2e36;
  --accent:#7fb3d5; --weak:#ff8f8a; --sound:#6fd9a4; --warnbg:#262017;
  color-scheme:dark; }

*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);
  font-size:16.5px;line-height:1.75;-webkit-text-size-adjust:100%}
.wrap{max-width:760px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:0 72px}
a{color:var(--accent)}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}

/* 顶栏 */
.topbar{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;
  background:var(--bg);border-bottom:1px solid var(--rule)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);
  z-index:21;background:var(--bg)}
.topbar .wrap{display:flex;align-items:center;gap:12px;padding-block:10px;flex-wrap:wrap}
.brand{font-family:var(--display);font-weight:700;font-size:14.5px;letter-spacing:.01em;
  color:var(--ink);text-decoration:none;white-space:nowrap}
.brand span{color:var(--muted);font-weight:500}
.topnav{margin-left:auto;display:flex;gap:4px;flex-wrap:wrap}
.topnav a{font-family:var(--mono);font-size:12px;text-decoration:none;color:var(--muted);
  padding:3px 7px;border-radius:4px;min-width:28px;text-align:center}
.topnav a:hover{background:var(--surface-2);color:var(--ink)}
.topnav a[aria-current]{background:var(--accent);color:var(--bg);font-weight:600}

/* 课头 */
.lesson-head{padding-block:40px 8px;border-bottom:1px solid var(--rule);margin-bottom:32px}
.kicker{font-family:var(--mono);font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--accent);margin:0 0 10px}
h1{font-family:var(--display);font-size:clamp(28px,6vw,40px);line-height:1.2;margin:0 0 10px;
  letter-spacing:-.015em;text-wrap:balance;font-weight:700}
.sub{color:var(--muted);font-size:14.5px;margin:0 0 28px;font-family:var(--mono)}

/* 大白话 */
.plain{background:var(--surface);border:1px solid var(--rule);border-left:4px solid var(--accent);
  border-radius:0 10px 10px 0;padding:22px 24px;margin:0 0 40px;font-size:17.5px;line-height:1.8}
.plain .tag{display:block;font-family:var(--mono);font-size:11.5px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);margin-bottom:12px;font-weight:600}
.plain p{margin:0 0 16px}
.plain p:last-child{margin-bottom:0}
.plain blockquote{margin:16px 0;padding:12px 16px;background:var(--surface-2);border-radius:8px;
  font-family:var(--mono);font-size:14px;line-height:1.7;border:0}

h2{font-family:var(--display);font-size:22px;margin:44px 0 14px;letter-spacing:-.01em;text-wrap:balance}
h3{font-family:var(--display);font-size:17.5px;margin:34px 0 10px;letter-spacing:-.005em}
h4{font-family:var(--display);font-size:15.5px;margin:0 0 8px}
p{margin:0 0 16px}
ul,ol,dl{margin:0 0 16px;padding-left:1.4em}
li{margin:0 0 8px}
dl{padding-left:0} dt{font-weight:600;margin-top:12px} dd{margin:0 0 8px 1.2em;color:var(--muted)}
strong{font-weight:650}
blockquote{margin:20px 0;padding:14px 18px;border-left:3px solid var(--rule);
  color:var(--ink);background:var(--surface);border-radius:0 8px 8px 0}
blockquote cite{display:block;margin-top:8px;font-style:normal;font-size:13.5px;color:var(--muted)}
code{font-family:var(--mono);font-size:.88em;background:var(--surface-2);
  padding:.12em .36em;border-radius:4px;word-break:break-word}
pre{background:var(--surface);border:1px solid var(--rule);border-radius:9px;
  padding:14px 16px;overflow-x:auto;margin:0 0 16px}
pre code{background:none;padding:0;font-size:13px;line-height:1.65;white-space:pre}

/* 表 */
.tw{overflow-x:auto;margin:0 0 20px;border:1px solid var(--rule);border-radius:9px}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:0}
th,td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-family:var(--display);font-weight:600;font-size:13.5px;background:var(--surface-2);
  white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
td:first-child{font-variant-numeric:tabular-nums}

/* 提示块 */
.callout{background:var(--surface);border:1px solid var(--rule);border-radius:10px;
  padding:18px 20px;margin:0 0 20px}
.callout p:last-child,.callout ul:last-child,.callout ol:last-child{margin-bottom:0}
.callout.warn{background:var(--warnbg);border-color:color-mix(in srgb,var(--weak) 30%,var(--rule))}
.callout.good{border-color:color-mix(in srgb,var(--sound) 40%,var(--rule))}

/* 动图 */
figure{margin:28px 0;border:1px solid var(--rule);border-radius:10px;overflow:hidden;
  background:var(--surface)}
figure svg,figure img{display:block;width:100%;height:auto;max-width:100%}
figcaption{padding:11px 16px;font-size:13.5px;color:var(--muted);border-top:1px solid var(--rule);
  background:var(--surface-2)}

/* 跑一下 */
.run{margin:0 0 20px}
.run-item{border:1px solid var(--rule);border-radius:9px;margin:0 0 12px;overflow:hidden;
  background:var(--surface)}
.cmdbar{display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--surface-2);
  border-bottom:1px solid var(--rule)}
.cmdbar code{background:none;padding:0;font-size:13px;flex:1;min-width:0;overflow-x:auto;
  white-space:pre}
.copy{flex:none;font-family:var(--mono);font-size:11.5px;border:1px solid var(--rule);
  background:var(--surface);color:var(--muted);border-radius:5px;padding:3px 9px;cursor:pointer}
.copy:hover{color:var(--ink);border-color:var(--accent)}
.copy[data-done]{color:var(--sound);border-color:var(--sound)}
.run-item p{margin:0;padding:11px 14px;font-size:14.5px;color:var(--muted)}

/* 证据分级 */
.ev{font-family:var(--mono);font-size:11px;padding:2px 7px;border-radius:999px;
  border:1px solid currentColor;white-space:nowrap}
.ev-s{color:var(--sound)} .ev-m{color:var(--accent)} .ev-w{color:var(--weak)}

/* 带走 */
.takeaway{background:var(--surface-2);border-radius:10px;padding:20px 22px;margin:36px 0 0;
  border:1px solid var(--rule)}
.takeaway .tag{font-family:var(--mono);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);display:block;margin-bottom:10px}
.takeaway p:last-child{margin-bottom:0}

/* 上一课 / 下一课 */
.pager{display:flex;gap:12px;margin-top:48px;padding-top:24px;border-top:1px solid var(--rule);
  flex-wrap:wrap}
.pager a{flex:1 1 220px;min-width:0;text-decoration:none;border:1px solid var(--rule);
  border-radius:10px;padding:14px 16px;background:var(--surface);color:var(--ink)}
.pager a:hover{border-color:var(--accent)}
.pager .dir{display:block;font-family:var(--mono);font-size:11.5px;color:var(--muted);
  margin-bottom:4px}
.pager .ttl{font-family:var(--display);font-size:15px;font-weight:600}
.pager .next{text-align:right}

/* 首页 */
.hero{padding-block:48px 8px}
.toc{display:grid;gap:10px;margin:0 0 40px;padding:0;list-style:none}
.toc a{display:flex;gap:14px;align-items:baseline;text-decoration:none;border:1px solid var(--rule);
  border-radius:10px;padding:14px 16px;background:var(--surface);color:var(--ink)}
.toc a:hover{border-color:var(--accent)}
.toc .num{font-family:var(--mono);font-size:13px;color:var(--accent);flex:none;font-weight:600}
.toc .body{min-width:0}
.toc .ttl{font-family:var(--display);font-weight:600;font-size:16px;display:block;line-height:1.4}
.toc .sub2{font-size:13.5px;color:var(--muted);display:block;margin-top:2px}
.disclaim{border:1px solid color-mix(in srgb,var(--weak) 35%,var(--rule));border-radius:10px;
  padding:16px 18px;margin:0 0 32px;background:var(--warnbg);font-size:14.5px}
.disclaim strong{color:var(--weak)}
footer{margin-top:56px;padding-top:22px;border-top:1px solid var(--rule);
  font-size:13.5px;color:var(--muted)}
footer a{color:var(--muted)}
@media (max-width:520px){
  body{font-size:16px}
  .plain{font-size:16.5px;padding:18px 18px}
  .brand span{display:none}
  .topbar .wrap{padding-block:8px;gap:8px;flex-wrap:nowrap}
  .topnav{overflow-x:auto;flex-wrap:nowrap;-webkit-overflow-scrolling:touch;
    scrollbar-width:none;mask-image:linear-gradient(90deg,#000 88%,transparent)}
  .topnav::-webkit-scrollbar{display:none}
  .topnav a{font-size:11.5px;padding:3px 6px;min-width:0;flex:none}
}
"""

JS = """
document.querySelectorAll('.copy').forEach(function(b){
  b.addEventListener('click', function(){
    var t = b.closest('.cmdbar').querySelector('code').textContent;
    function done(){ b.dataset.done='1'; b.textContent='已复制';
      setTimeout(function(){ delete b.dataset.done; b.textContent='复制'; }, 1600); }
    try {
      navigator.clipboard.writeText(t).then(done, select);
    } catch(e){ select(); }
    function select(){
      var r=document.createRange(); r.selectNodeContents(b.closest('.cmdbar').querySelector('code'));
      var s=getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent='已选中，按 ⌘C';
      setTimeout(function(){ b.textContent='复制'; }, 2400);
    }
  });
});
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap">')


def md(text):
    """极小的 markdown：**粗体**、`代码`、> 引用、段落。"""
    out, buf, quote = [], [], []

    def flush():
        if buf:
            out.append("<p>" + inline("\n".join(buf)) + "</p>")
            buf.clear()

    def flushq():
        if quote:
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            quote.clear()

    for line in text.split("\n"):
        if line.startswith("> "):
            flush()
            quote.append(line[2:].strip())
        elif not line.strip():
            flush()
            flushq()
        else:
            flushq()
            buf.append(line.strip())
    flush()
    flushq()
    return "\n".join(out)


def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s.replace("\n", "<br>")


def ev_class(e):
    if e.startswith(("很强", "强")):
        return "ev-s"
    if e.startswith("中"):
        return "ev-m"
    return "ev-w"


def nav(cur=None):
    items = ['<a href="index.html"%s>目录</a>' % (' aria-current="page"' if cur is None else "")]
    for L in LESSONS:
        a = ' aria-current="page"' if cur == L["n"] else ""
        items.append('<a href="%02d-%s.html"%s title="%s">%02d</a>'
                     % (L["n"], L["slug"], a, html.escape(L["title"]), L["n"]))
    return '<nav class="topnav">' + "".join(items) + "</nav>"


def topbar(cur=None):
    return ('<header class="topbar"><div class="wrap">'
            '<a class="brand" href="index.html">弱熵的统一规律 <span>· 一门可以自己跑的课</span></a>'
            + nav(cur) + "</div></header>")


def inline_svg(name):
    p = os.path.join(DOCS, "assets", name)
    with open(p, encoding="utf-8") as f:
        s = f.read()
    return re.sub(r"<\?xml[^>]*\?>", "", s).strip()


def runs_html(runs):
    parts = ['<h2>自己跑一下</h2>', '<div class="run">']
    for cmd, what in runs:
        parts.append(
            '<div class="run-item"><div class="cmdbar"><code>%s</code>'
            '<button class="copy" type="button">复制</button></div>'
            '<p>%s</p></div>' % (html.escape(cmd), inline(what)))
    parts.append("</div>")
    return "\n".join(parts)


def numbers_html(rows):
    parts = ['<h2>数字与出处</h2>',
             '<div class="tw"><table><thead><tr><th>数字</th><th>是什么</th>'
             '<th>出处</th><th>证据</th></tr></thead><tbody>']
    for val, what, src, ev in rows:
        parts.append('<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td>'
                     '<td><span class="ev %s">%s</span></td></tr>'
                     % (inline(val), inline(what), inline(src), ev_class(ev), html.escape(ev)))
    parts.append("</tbody></table></div>")
    return "\n".join(parts)


DISCLAIMER = ('<div class="disclaim"><strong>免责：</strong>'
              '本课程复现的全部是<strong>已被公开披露并已修复</strong>的历史缺陷，用于教学。'
              '所有实验使用固定的 demo 种子，不生成任何真实钱包，不联网，不查询任何地址。'
              'Coldcard 相关材料全部来自外部公开出处。</div>')


def lesson_body(L, i):
    p = []
    p.append('<div class="lesson-head">')
    p.append('<p class="kicker">第 %02d 课 / 共 %d 课</p>' % (L["n"], len(LESSONS)))
    p.append("<h1>%s</h1>" % html.escape(L["title"]))
    p.append('<p class="sub">%s</p>' % html.escape(L["sub"]))
    p.append("</div>")
    p.append('<div class="plain"><span class="tag">大白话</span>%s</div>' % md(L["plain"]))
    if L.get("anim"):
        p.append("<figure>%s<figcaption>%s</figcaption></figure>"
                 % (inline_svg(L["anim"]), inline(L["anim_caption"])))
    p.append("<h2>往下一层</h2>")
    p.append(L["body"])
    p.append(runs_html(L["run"]))
    p.append(numbers_html(L["numbers"]))
    p.append('<div class="takeaway"><span class="tag">带走这个</span>%s</div>' % md(L["takeaway"]))
    prev = LESSONS[i - 1] if i > 0 else None
    nxt = LESSONS[i + 1] if i < len(LESSONS) - 1 else None
    pg = ['<nav class="pager">']
    if prev:
        pg.append('<a href="%02d-%s.html"><span class="dir">← 上一课</span>'
                  '<span class="ttl">%s</span></a>' % (prev["n"], prev["slug"], html.escape(prev["title"])))
    else:
        pg.append('<a href="index.html"><span class="dir">← 回到</span>'
                  '<span class="ttl">目录</span></a>')
    if nxt:
        pg.append('<a class="next" href="%02d-%s.html"><span class="dir">下一课 →</span>'
                  '<span class="ttl">%s</span></a>' % (nxt["n"], nxt["slug"], html.escape(nxt["title"])))
    else:
        pg.append('<a class="next" href="index.html"><span class="dir">课程结束 →</span>'
                  '<span class="ttl">回到目录</span></a>')
    pg.append("</nav>")
    p.append("\n".join(pg))
    p.append(footer())
    return "\n".join(p)


SHORT_DISCLAIMER = (
    '<div class="disclaim"><strong>免责：</strong>本课复现的是'
    '<strong>已被公开披露并已修复</strong>的历史缺陷，用于教学。'
    '固定 demo 种子，不联网，不碰任何真实密钥。'
    '如果你怀疑自己的钱包受影响，不要用这里的代码去验证 —— 去看厂商官方公告。</div>')


def footer():
    return (SHORT_DISCLAIMER
            + '<footer><p>%s · 代码与动图：<a href="%s">GitHub</a>。'
            '每一课的代码都能用 <code>python3</code> 一行跑出结果。</p>'
            '<p>所有数字带出处和证据分级。标「弱」的不要单独使用。</p></footer>'
            % (html.escape(COURSE), REPO))


def index_body():
    p = ['<div class="hero">',
         '<p class="kicker">一门可以自己跑的课 · 共 %d 课</p>' % len(LESSONS),
         "<h1>%s</h1>" % html.escape(COURSE),
         '<p class="sub">%s</p>' % html.escape(SUBTITLE),
         "</div>",
         '<div class="plain"><span class="tag">先看这个</span>%s</div>' % md(INTRO_PLAIN),
         DISCLAIMER,
         "<h2>课程目录</h2>", '<ul class="toc">']
    for L in LESSONS:
        p.append('<li><a href="%02d-%s.html"><span class="num">%02d</span>'
                 '<span class="body"><span class="ttl">%s</span>'
                 '<span class="sub2">%s</span></span></a></li>'
                 % (L["n"], L["slug"], L["n"], html.escape(L["title"]), html.escape(L["sub"])))
    p.append("</ul>")
    p.append("""
<h2>怎么开始</h2>
<p>整套代码只用 Python 标准库，没有任何依赖。椭圆曲线、BIP39、BIP32、MT19937
全部在仓库里从头实现 —— 因为这门课的要点就是<strong>不要相信包装层</strong>，
包括我写的那些。</p>
<div class="run">
<div class="run-item"><div class="cmdbar"><code>git clone %s.git &amp;&amp; cd weak-entropy-lessons</code>
<button class="copy" type="button">复制</button></div><p>克隆下来。</p></div>
<div class="run-item"><div class="cmdbar"><code>./run_all.sh -q</code>
<button class="copy" type="button">复制</button></div>
<p>把十二课全部跑一遍，确认每一课都真的能跑出结果（约 40 秒）。</p></div>
<div class="run-item"><div class="cmdbar"><code>python3 lessons/01_milk_sad/milk_sad.py</code>
<button class="copy" type="button">复制</button></div>
<p>从第一课开始。它会逐字复现那二十四个词，然后在几秒内反推出一把钥匙。</p></div>
</div>

<h2>这门课的三条规矩</h2>
<ol>
<li><strong>大白话在前，细节在后。</strong>每课开头那个方框几乎不含数字 ——
只想拿一个心智模型就走，看它就够了。</li>
<li><strong>每个数字都能指回出处，而且带证据分级。</strong>
标「弱」的数字不要单独使用，哪怕它是流传最广的那个。</li>
<li><strong>能跑的就不要只是读。</strong>十二课里有十一课可以在一台笔记本上跑完，
包括用真的编译器复现 Coldcard 那个链接期失效。</li>
</ol>
""" % REPO)
    p.append('<footer><p>%s · 代码与动图：<a href="%s">GitHub</a>。</p>'
             '<p>所有数字带出处和证据分级。标「弱」的不要单独使用。</p></footer>'
             % (html.escape(COURSE), REPO))
    return "\n".join(p)


def page(title, body, cur=None, standalone=True):
    head = ('<title>%s</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            '%s\n<style>%s</style>' % (html.escape(title), FONTS, CSS))
    inner = ('%s\n<main class="wrap">\n%s\n</main>\n<script>%s</script>'
             % (topbar(cur), body, JS))
    if not standalone:
        return head + "\n" + inner
    return ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '%s\n</head>\n<body>\n%s\n</body>\n</html>\n' % (head, inner))


def main():
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(ART, exist_ok=True)
    written = []
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(COURSE, index_body(), None))
    written.append("docs/index.html")
    for i, L in enumerate(LESSONS):
        name = "%02d-%s.html" % (L["n"], L["slug"])
        t = "%s · 第 %02d 课" % (L["title"], L["n"])
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(page(t, lesson_body(L, i), L["n"]))
        written.append("docs/" + name)
        shutil.copyfile(os.path.join(DOCS, name), os.path.join(ART, name))
    # Artifact 主页：不带 doctype/html/head 外壳（平台会包）
    with open(os.path.join(ART, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(COURSE, index_body(), None, standalone=False))
    written.append("artifact/index.html + 12 课副本")
    with open(os.path.join(DOCS, ".nojekyll"), "w") as f:
        f.write("")
    for w in written:
        print(" ", w)
    print(f"\n共 {len(LESSONS) + 1} 页。")


if __name__ == "__main__":
    main()
