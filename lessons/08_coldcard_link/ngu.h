#ifndef NGU_H
#define NGU_H
#include <stdint.h>

/* 这就是 libngu（Coinkite 自家密码库）里那一行。
 *
 *     extern uint32_t rng_get(void);
 *
 * 「声明有这么个函数，但不说它在哪。」
 * 由**链接器**在组装固件时去找一个叫 rng_get 的全局符号。
 *
 * 这一行是整个 1,962 天事故的全部内容。它看起来完全正常。
 */
extern uint32_t rng_get(void);

/* libngu 打算做的事情是完全正确的：
 * 读硬件真随机数，再 XOR 上一个软件 PRNG —— 这是标准的加固做法。 */
void ngu_random_bytes(uint8_t *out, int len);
uint32_t ngu_random_word(void);

#endif
