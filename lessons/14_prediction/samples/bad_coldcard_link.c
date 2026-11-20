/* 转录自 Coldcard 的形状（第 8 课有可跑的完整版）。
 * 一行 extern，1,962 天，2^22。 */
#include <stdint.h>
extern uint32_t rng_get(void);        /* ← 由链接器决定它是谁 */

static uint32_t sw_prng(void);

uint32_t ngu_random_word(void) {
    return rng_get() ^ sw_prng();     /* 本意：硬件 XOR 软件。实际：软件 XOR 软件 */
}
