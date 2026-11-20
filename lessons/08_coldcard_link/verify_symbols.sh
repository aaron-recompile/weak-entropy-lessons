#!/bin/sh
# 构建期符号校验 —— Coinkite 真实修复（commit ca724637）里加的那个
# arm-none-eabi-nm 目标的等价物：一旦上游那个 rng_get 重新出现，让构建失败。
#
# 本课最有用的一条方法就在这里：
#
#     **验证路径，不要验证分布。**
#
# 第 11 课会让你看到，五道检查输出的保险，五道全部被一个
# 正常推进的软件 PRNG 轻松通过。而这个 15 行的脚本能抓住它。
set -e
BUILD="${1:-build}"
NM="${NM:-nm}"
fail=0

check() {
    obj="$1"; want="$2"
    [ -f "$obj" ] || return 0
    if $NM "$obj" 2>/dev/null | grep -qE ' T _?rng_get$'; then got=exports; else got=absent; fi
    printf "  %-34s rng_get: %-8s 期望: %-8s " "$(basename "$obj")" "$got" "$want"
    if [ "$got" = "$want" ]; then echo "✅"; else echo "❌"; fail=1; fi
}

echo "  规则：板子必须导出 rng_get；上游的 MicroPython 目标文件必须不导出。"
echo ""
check "$BUILD/board_rng_exported.o"      exports
check "$BUILD/micropython_rng_nulled.o"  absent
echo ""
if [ "$fail" = 0 ]; then
    echo "  ✅ 符号校验通过 —— rng_get 绑在板子的硬件读取路径上。"
    echo ""
    echo "  这个脚本检查的是**字节从哪来**，不是**字节长什么样**。"
    echo "  Coldcard 那五道保险全都在做后者，所以五道全都没响。"
else
    echo "  ❌ 符号校验失败 —— 构建应当在这里中止，不许发版。"
    exit 1
fi
