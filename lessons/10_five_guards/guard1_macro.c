/* 保险之一：构建期守卫。
 *
 * 真实固件里是这一条：
 *     #ifndef MICROPY_HW_ENABLE_RNG
 *     #error "get a HW TRNG plz"
 *     #endif
 *
 * 它测的是这个宏**有没有被定义**，而不是它的**值**。
 * 而 STM32 的 mpconfigboard_common.h **总是**定义它，默认 0。
 *
 *     用 -DGUARD_STYLE=ifndef 编译（真实固件的写法）→ 编译通过。守卫没响。
 *     用 -DGUARD_STYLE=value  编译（正确的写法）    → #error，构建中止。
 */
#include <stdio.h>

/* 这一行模拟 mpconfigboard_common.h 做的事 */
#define MICROPY_HW_ENABLE_RNG 0

#if GUARD_STYLE_IFNDEF
  #ifndef MICROPY_HW_ENABLE_RNG
    #error "get a HW TRNG plz"
  #endif
  #define WHICH "ifndef（真实固件的写法）"
#else
  #if !MICROPY_HW_ENABLE_RNG
    #error "get a HW TRNG plz —— 这次真的响了"
  #endif
  #define WHICH "检查值（正确的写法）"
#endif

int main(void) {
    printf("  编译通过了。守卫形式：%s\n", WHICH);
    printf("  MICROPY_HW_ENABLE_RNG 的值 = %d\n", MICROPY_HW_ENABLE_RNG);
    return 0;
}
