/* libngu：Coinkite 自家的密码库。
 * 它不知道、也不该知道 rng_get 的实现在哪 —— 那是链接器的事。 */
#include "ngu.h"

/* 一个软件 PRNG，用来和硬件随机数混合。
 * 单独看它没问题：标准做法就是「物理噪声 XOR 软件生成器」，
 * 这样即使软件生成器被预测，物理噪声还在。 */
static uint32_t sw_state = 0x6C078965u;

static uint32_t sw_prng(void) {
    sw_state ^= sw_state << 13;
    sw_state ^= sw_state >> 17;
    sw_state ^= sw_state << 5;
    return sw_state;
}

uint32_t ngu_random_word(void) {
    /* 这一行是整条链里的意图所在：
     *   硬件真随机数  XOR  软件 PRNG
     * 本来应该是「不可预测 XOR 可预测 = 不可预测」。 */
    return rng_get() ^ sw_prng();
}

void ngu_random_bytes(uint8_t *out, int len) {
    for (int i = 0; i < len; i += 4) {
        uint32_t w = ngu_random_word();
        for (int j = 0; j < 4 && i + j < len; j++)
            out[i + j] = (uint8_t)(w >> (8 * j));
    }
}
