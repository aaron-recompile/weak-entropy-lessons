// 转录自 2022-11 Trust Wallet 浏览器扩展的 Wasm 随机数包装层。
// CVE-2023-31290。32 位种子 = 80 GB 的表。
// 「为什么会有这个包装层」：Wasm 里读不到 /dev/urandom。理由听起来完全合理。
#include <random>
#include <ctime>

void secure_random_generator(uint8_t* out, size_t len) {
    std::mt19937 gen(static_cast<uint32_t>(time(NULL)));
    std::uniform_int_distribution<int> dist(0, 255);
    for (size_t i = 0; i < len; i++) out[i] = dist(gen);
}
