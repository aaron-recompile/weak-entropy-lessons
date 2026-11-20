/* 固件主程序：生成一个 32 字节「种子」，打印出来。
 * 它只调用 ngu_random_bytes —— 完全不知道随机数从哪来。 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "ngu.h"

int main(void) {
    uint8_t seed[32];
    ngu_random_bytes(seed, sizeof seed);

    printf("种子（32 字节）: ");
    for (int i = 0; i < 32; i++) printf("%02x", seed[i]);
    printf("\n");

    /* 保险之三（真实固件里的）：
     *     assert len(set(seed)) > 4
     * 32 字节里至少 5 个不同的值。记住这条，第 10 课要用。 */
    int seen[256] = {0}, distinct = 0;
    for (int i = 0; i < 32; i++) if (!seen[seed[i]]++) distinct++;
    printf("32 字节里有 %d 个不同的值（断言要求 > 4）: %s\n",
           distinct, distinct > 4 ? "通过 ✅" : "失败 ❌");
    return 0;
}
