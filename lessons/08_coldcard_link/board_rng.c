/* 板子自己的 rng.c —— 这里是**真的**读硬件真随机数发生器寄存器的地方。
 *
 * 硬件一直是好的。芯片里那个 TRNG 从来没坏过。
 * 问题只有一个：下面这个函数的 `static`。
 *
 *   static  ==  只对本编译单元可见  ==  不导出全局符号
 *
 * 所以链接器在找 rng_get 的时候，**看不见它**。
 */
#include <stdint.h>
#include <stdio.h>

/* 模拟 STM32 的 RNG->DR 寄存器。真机上这是物理噪声。
 * 这里用 /dev/urandom 代替，为了让「硬件路径」在本机上也是真的不可预测。 */
static uint32_t CHIP_TRNG_32(void) {
    uint32_t v = 0;
    FILE *f = fopen("/dev/urandom", "rb");
    if (f) { if (fread(&v, 4, 1, f) != 1) v = 0; fclose(f); }
    return v;
}

#ifdef EXPORT_BOARD_RNG
/* make duplicate / make fixed 用这一侧：把 static 去掉，导出全局符号。 */
uint32_t rng_get(void)
#else
/* 出事的那一侧：static。*/
static uint32_t rng_get_or_fault(void)
#endif
{
    uint32_t a = CHIP_TRNG_32();
    uint32_t b = CHIP_TRNG_32();
    /* 真实固件里的运行期守卫，保险之二：
     *   if (chip == last) fail hard;   「也许 TRNG 没上时钟？」
     * 它只比较前后两个输出字。记住这一条，第 11 课要用。 */
    if (a == b) {
        fprintf(stderr, "TRNG 返回了两个一样的字 —— 变砖\n");
        __builtin_trap();
    }
    return a;
}

#ifndef EXPORT_BOARD_RNG
/* static 函数不被调用会触发警告，这里给它一个「本地用户」。
 * 真实固件里它也有本地调用者 —— 所以编译器不会抱怨，
 * **也不会有任何人收到任何提示。** */
uint32_t board_rng_local_only(void) { return rng_get_or_fault(); }
#endif
