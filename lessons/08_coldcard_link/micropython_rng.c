/* MicroPython 的 ports/stm32/rng.c。
 *
 * 它**导出了**一个全局 rng_get。实现是一个软件 PRNG，
 * 上游注释里写得明明白白：这是给「没有 RNG 的 MCU」准备的。
 *
 * ⚠️ 证据说明：MicroPython 那个软件 fallback 叫 Yasmarang。
 *    下面这段按公开分析的描述复写 —— 结构（32 位种子 → 确定性流）与原版一致，
 *    但**逐行是否与上游完全一致，我没有核对过**。
 *    这不影响本课要演示的东西：本课演示的是**链接器怎么绑错符号**，
 *    那一部分是精确的、可以在你自己机器上独立验证的。
 */
#include <stdint.h>

/* 种子的两个输入，XOR 进同一个 32 位字里（所以不叠加）： */

/* ① 芯片唯一标识符的 32 位。这些位编码的是**晶片在晶圆上的坐标**。
 *    按 Wizardsardine 的模型最多 14 位携带信息，其中 12 位可达
 *    → Mk3 上大约 3,300 个位置。
 *    **这个值既不变，也不保密。** 它印在芯片上。 */
static uint32_t chip_uid_word(void) {
    /* 固定的 demo 值，代表某一颗具体的芯片。真机上读 UID_BASE。 */
    return 0x0041002Au;
}

/* ② SysTick —— 一个每毫秒回绕一次的计数器。 */
static uint32_t systick_val(void) {
    return 1234u;                     /* demo：开机后固定的某一刻 */
}

static uint32_t ys_pad = 0, ys_n = 0, ys_d = 0;
static uint8_t  ys_dat = 0;

static uint32_t yasmarang(void) {
    ys_pad += ys_dat + ys_d * ys_n;
    ys_pad = (ys_pad << 3) + (ys_pad >> 29);
    ys_n = ys_pad | 2;
    ys_d ^= (ys_pad << 31) + (ys_pad >> 1);
    ys_dat ^= (uint8_t)ys_pad ^ (uint8_t)(ys_d >> 8) ^ 1;
    return ys_pad ^ (ys_d << 5) ^ (ys_pad >> 18) ^ ((uint32_t)ys_dat << 1);
}

/* ← 这个是全局的。链接器找得到它。 */
uint32_t rng_get(void) {
    if (ys_pad == 0)
        ys_pad = chip_uid_word() ^ systick_val();
    return yasmarang();
}
