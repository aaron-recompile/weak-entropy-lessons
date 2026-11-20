# 第 7 课 · Coldcard 的链接期符号绑定
#
#   make broken      出事的那个构建：链接成功，绑到软件 PRNG 上
#   make duplicate   把 static 去掉 → 构建直接因重复符号失败
#   make fixed       Coinkite 的真实修复：导出自己的，把上游那个编译掉
#   make verify      构建期符号校验（真实修复里的 nm 目标）
#   make all         依次跑完三个，这是本课的正确跑法
#   make clean

CC      ?= cc
CFLAGS  ?= -O1 -Wall -std=c11
NM      ?= nm
BUILD   := build

.PHONY: all broken duplicate archive fixed verify clean

all: broken duplicate archive fixed verify
	@echo ""
	@echo "════════════════════════════════════════════════════════════════"
	@echo " 三个构建都跑完了。把 broken 和 fixed 的输出对照着看一遍。"
	@echo " 然后记住 Wizardsardine 那句话："
	@echo "   「这次失败，恰恰来自那个冲突的缺席。」"
	@echo "════════════════════════════════════════════════════════════════"

$(BUILD):
	@mkdir -p $(BUILD)

# ──────────────────────────────────────────────────────────────────────
# ① 出事的那个构建
# ──────────────────────────────────────────────────────────────────────
broken: | $(BUILD)
	@echo ""
	@echo "──────────────────────────────────────────────────────────────"
	@echo "① make broken —— 2021-03 到 2026-07 的那个构建"
	@echo "──────────────────────────────────────────────────────────────"
	@echo "  board_rng.c 里的读取函数是 static（不导出 rng_get）"
	@echo "  micropython_rng.c 导出了一个全局 rng_get（软件 PRNG）"
	@echo ""
	$(CC) $(CFLAGS) -c main.c            -o $(BUILD)/main.o
	$(CC) $(CFLAGS) -c libngu.c          -o $(BUILD)/libngu.o
	$(CC) $(CFLAGS) -c board_rng.c       -o $(BUILD)/board_rng.o
	$(CC) $(CFLAGS) -c micropython_rng.c -o $(BUILD)/micropython_rng.o
	@echo ""
	@echo "  谁导出了 rng_get？（T = 导出的代码符号，U = 未定义，要别人给）"
	@for o in main libngu board_rng micropython_rng; do \
	  printf "    %-22s " "$$o.o"; \
	  $(NM) $(BUILD)/$$o.o 2>/dev/null | grep -E ' [TUtu] _?rng_get$$' | sed 's/^/  /' | tr '\n' ' '; \
	  echo ""; \
	done
	@echo ""
	@echo "  → libngu.o 要一个 rng_get（U）。只有 micropython_rng.o 给得出（T）。"
	@echo "    链接器在这里**并不是在两个候选里挑了一个 —— 这里只有一个候选。**"
	@echo ""
	$(CC) $(BUILD)/main.o $(BUILD)/libngu.o $(BUILD)/board_rng.o $(BUILD)/micropython_rng.o -o $(BUILD)/fw_broken
	@echo "  ✅ 链接成功。没有警告。没有错误。固件可以发版。"
	@echo ""
	@echo "  跑三次："
	@for i in 1 2 3; do printf "    "; ./$(BUILD)/fw_broken | head -1; done
	@echo ""
	@echo "  ⚠️  三次一模一样。**这台设备每次开机都生成同一个种子。**"
	@echo "     而硬件 TRNG 好得很 —— 它只是从来没有被调用过。"

# ──────────────────────────────────────────────────────────────────────
# ② 本课的punchline
# ──────────────────────────────────────────────────────────────────────
duplicate: | $(BUILD)
	@echo ""
	@echo "──────────────────────────────────────────────────────────────"
	@echo "② make duplicate —— 把 board_rng.c 的 static 去掉，会发生什么"
	@echo "──────────────────────────────────────────────────────────────"
	$(CC) $(CFLAGS) -c main.c            -o $(BUILD)/main.o
	$(CC) $(CFLAGS) -c libngu.c          -o $(BUILD)/libngu.o
	$(CC) $(CFLAGS) -DEXPORT_BOARD_RNG -c board_rng.c -o $(BUILD)/board_rng_exported.o
	$(CC) $(CFLAGS) -c micropython_rng.c -o $(BUILD)/micropython_rng.o
	@echo ""
	@echo "  现在两个目标文件都导出 rng_get："
	@printf "    board_rng_exported.o  "; $(NM) $(BUILD)/board_rng_exported.o | grep -E ' T _?rng_get$$' || true
	@printf "    micropython_rng.o     "; $(NM) $(BUILD)/micropython_rng.o    | grep -E ' T _?rng_get$$' || true
	@echo ""
	@echo "  链接："
	@if $(CC) $(BUILD)/main.o $(BUILD)/libngu.o $(BUILD)/board_rng_exported.o \
	        $(BUILD)/micropython_rng.o -o $(BUILD)/fw_dup 2> $(BUILD)/dup.log; then \
	  echo "  ⚠️  这台机器的链接器没有报错（见 README 里关于归档/弱符号的说明）"; \
	else \
	  echo "  ❌ 构建失败。链接器的原话："; \
	  sed 's/^/      /' $(BUILD)/dup.log | head -8; \
	  echo ""; \
	  echo "  → **这就是本课的全部。**"; \
	  echo "    要是 Coinkite 导出了自己的 rng_get，就会有两个同名全局定义，"; \
	  echo "    构建会在 2021 年 3 月的那一天直接红掉，没有人会丢一分钱。"; \
	  echo ""; \
	  echo "      「这次失败，恰恰来自那个冲突的缺席。」—— Wizardsardine"; \
	fi

# ──────────────────────────────────────────────────────────────────────
# ②b 链接器的第二个坑：同样两个定义，放进 .a 里就**不报错了**
# ──────────────────────────────────────────────────────────────────────
archive: | $(BUILD)
	@echo ""
	@echo "──────────────────────────────────────────────────────────────"
	@echo "②b make archive —— 为什么真实固件里更难发现"
	@echo "──────────────────────────────────────────────────────────────"
	@echo "  刚才那个 duplicate symbol 错误，前提是两个**目标文件**都在命令行上。"
	@echo "  但真实构建里，这些东西常常是先打包成静态库（.a）再链接的。"
	@echo "  归档的语义完全不同：**链接器只取它需要的那个成员，先出现的赢，不报错。**"
	@echo ""
	$(CC) $(CFLAGS) -c main.c   -o $(BUILD)/main.o
	$(CC) $(CFLAGS) -c libngu.c -o $(BUILD)/libngu.o
	$(CC) $(CFLAGS) -DEXPORT_BOARD_RNG -c board_rng.c -o $(BUILD)/board_rng_exported.o
	$(CC) $(CFLAGS) -c micropython_rng.c -o $(BUILD)/micropython_rng.o
	@rm -f $(BUILD)/libmp.a $(BUILD)/libboard.a
	@ar rcs $(BUILD)/libmp.a    $(BUILD)/micropython_rng.o
	@ar rcs $(BUILD)/libboard.a $(BUILD)/board_rng_exported.o
	@echo "  顺序 A：先 libmp.a（软件 PRNG）"
	@$(CC) $(BUILD)/main.o $(BUILD)/libngu.o $(BUILD)/libmp.a $(BUILD)/libboard.a \
	       -o $(BUILD)/fw_arch_a 2>/dev/null && printf "    " && ./$(BUILD)/fw_arch_a | head -1
	@echo "  顺序 B：先 libboard.a（硬件）"
	@$(CC) $(BUILD)/main.o $(BUILD)/libngu.o $(BUILD)/libboard.a $(BUILD)/libmp.a \
	       -o $(BUILD)/fw_arch_b 2>/dev/null && printf "    " && ./$(BUILD)/fw_arch_b | head -1
	@echo ""
	@echo "  两次链接都**成功**，没有任何警告 —— 但绑到了不同的实现上。"
	@echo "  顺序 A 每次开机同一个种子；顺序 B 每次都不一样。"
	@echo ""
	@echo "  → **你的钱包是否安全，取决于构建脚本里两个库的先后顺序。**"
	@echo "    这就是为什么第 ④ 步那个 nm 校验不是可选项。"

# ──────────────────────────────────────────────────────────────────────
# ③ 真实的修复（commit ca724637，2026-07-31）—— 全部在构建期
# ──────────────────────────────────────────────────────────────────────
fixed: | $(BUILD)
	@echo ""
	@echo "──────────────────────────────────────────────────────────────"
	@echo "③ make fixed —— Coinkite 2026-07-31 的真实修复"
	@echo "──────────────────────────────────────────────────────────────"
	@echo "  两步，都在构建期，一行运行期代码都没加："
	@echo "    1. 板子导出自己的全局 rng_get()"
	@echo "    2. 把 MicroPython 的那个目标文件**用 /dev/null 编译掉**"
	@echo ""
	$(CC) $(CFLAGS) -c main.c   -o $(BUILD)/main.o
	$(CC) $(CFLAGS) -c libngu.c -o $(BUILD)/libngu.o
	$(CC) $(CFLAGS) -DEXPORT_BOARD_RNG -c board_rng.c -o $(BUILD)/board_rng_exported.o
	$(CC) $(CFLAGS) -x c /dev/null -c -o $(BUILD)/micropython_rng_nulled.o
	@echo "  上游那个目标文件现在是空的："
	@printf "    micropython_rng_nulled.o  符号数 = "; $(NM) $(BUILD)/micropython_rng_nulled.o 2>/dev/null | wc -l | tr -d ' '
	@echo ""
	$(CC) $(BUILD)/main.o $(BUILD)/libngu.o $(BUILD)/board_rng_exported.o \
	      $(BUILD)/micropython_rng_nulled.o -o $(BUILD)/fw_fixed
	@echo "  ✅ 链接成功，而且这次绑到了硬件那一侧。跑三次："
	@for i in 1 2 3; do printf "    "; ./$(BUILD)/fw_fixed | head -1; done
	@echo ""
	@echo "  三次都不一样。注意：MICROPY_HW_ENABLE_RNG 仍然是 0，"
	@echo "  那个坏掉的 #ifndef 守卫也没动 —— **他们绕过了它，没有修它。**"

# ──────────────────────────────────────────────────────────────────────
# ④ 验证路径，不要验证分布
# ──────────────────────────────────────────────────────────────────────
verify: | $(BUILD)
	@echo ""
	@echo "──────────────────────────────────────────────────────────────"
	@echo "④ make verify —— 真实修复里那个 nm 校验目标"
	@echo "──────────────────────────────────────────────────────────────"
	@NM=$(NM) sh ./verify_symbols.sh $(BUILD)

clean:
	rm -rf $(BUILD)
