"""
MT19937 —— 40 行把「游戏和模拟用的随机数」写出来。

这不是从库里 import 的，是从头实现的，因为本课程的全部要点就是：
这个生成器的内部状态只有 624 个 32 位字，而且它完全由播种时喂进去的那个数决定。
喂同一个数，永远得到同一条流。

参考：Matsumoto & Nishimura 1998。Python 自带的 random 模块也是 MT19937，
但 random.seed(n) 走的是 init_by_array，和 C++ 的 std::mt19937(n)（init_genrand）
不是同一条流 —— 这个区别本身就是一课，见 lessons/02_milk_sad/。
"""

N, M = 624, 397
MATRIX_A = 0x9908B0DF
UPPER_MASK = 0x80000000
LOWER_MASK = 0x7FFFFFFF


class MT19937:
    def __init__(self, seed=0):
        self.mt = [0] * N
        self.mti = N + 1
        self.init_genrand(seed & 0xFFFFFFFF)

    def init_genrand(self, s):
        """C++ std::mt19937(s) / C 的 init_genrand(s) —— 32 位种子，一个数定全局。"""
        self.mt[0] = s & 0xFFFFFFFF
        for i in range(1, N):
            self.mt[i] = (1812433253 * (self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) + i) & 0xFFFFFFFF
        self.mti = N

    def genrand_uint32(self):
        if self.mti >= N:
            for i in range(N):
                y = (self.mt[i] & UPPER_MASK) | (self.mt[(i + 1) % N] & LOWER_MASK)
                self.mt[i] = self.mt[(i + M) % N] ^ (y >> 1) ^ (MATRIX_A if y & 1 else 0)
            self.mti = 0
        y = self.mt[self.mti]
        self.mti += 1
        # tempering
        y ^= y >> 11
        y = (y ^ ((y << 7) & 0x9D2C5680)) & 0xFFFFFFFF
        y = (y ^ ((y << 15) & 0xEFC60000)) & 0xFFFFFFFF
        y ^= y >> 18
        return y

    # --- 下面几个是为了复现各个真实案例里不同的「取字节」方式 ---

    def bytes_be(self, n):
        """每个 32 位输出按大端摊成 4 字节。"""
        out = bytearray()
        while len(out) < n:
            out += self.genrand_uint32().to_bytes(4, "big")
        return bytes(out[:n])

    def bytes_le(self, n):
        out = bytearray()
        while len(out) < n:
            out += self.genrand_uint32().to_bytes(4, "little")
        return bytes(out[:n])

    def bytes_low8(self, n):
        """每个 32 位输出只取最低字节 —— 很多 C++ 代码用
        uniform_int_distribution<uint8_t> 时的实际效果。浪费 24 位，
        但不影响搜索空间：空间大小由种子决定，不由每次取多少位决定。"""
        return bytes(self.genrand_uint32() & 0xFF for _ in range(n))

    def bytes_high8(self, n):
        return bytes(self.genrand_uint32() >> 24 for _ in range(n))


class MT19937_64:
    """std::mt19937_64。Milk Sad 的变体之一要用。"""
    NN, MM = 312, 156
    MATRIX_A = 0xB5026F5AA96619E9
    UM = 0xFFFFFFFF80000000
    LM = 0x7FFFFFFF

    def __init__(self, seed=0):
        self.mt = [0] * self.NN
        self.mt[0] = seed & 0xFFFFFFFFFFFFFFFF
        for i in range(1, self.NN):
            self.mt[i] = (6364136223846793005 * (self.mt[i - 1] ^ (self.mt[i - 1] >> 62)) + i) & 0xFFFFFFFFFFFFFFFF
        self.mti = self.NN

    def genrand_uint64(self):
        if self.mti >= self.NN:
            for i in range(self.NN):
                x = (self.mt[i] & self.UM) | (self.mt[(i + 1) % self.NN] & self.LM)
                self.mt[i] = self.mt[(i + self.MM) % self.NN] ^ (x >> 1) ^ (self.MATRIX_A if x & 1 else 0)
            self.mti = 0
        x = self.mt[self.mti]
        self.mti += 1
        x ^= (x >> 29) & 0x5555555555555555
        x ^= (x << 17) & 0x71D67FFFEDA60000
        x ^= (x << 37) & 0xFFF7EEE000000000
        x ^= x >> 43
        return x & 0xFFFFFFFFFFFFFFFF

    def bytes_be(self, n):
        out = bytearray()
        while len(out) < n:
            out += self.genrand_uint64().to_bytes(8, "big")
        return bytes(out[:n])

    def bytes_le(self, n):
        out = bytearray()
        while len(out) < n:
            out += self.genrand_uint64().to_bytes(8, "little")
        return bytes(out[:n])


if __name__ == "__main__":
    m = MT19937(0)
    print("std::mt19937(0) 的前 8 个输出：")
    for _ in range(8):
        print(" ", m.genrand_uint32())


# ---------------------------------------------------------------------------
# 攻击者会做的那个优化 —— 这一段本身就是一课。
#
# 爆破的时候，每个候选种子都要：624 次播种递推 + 624 次 twist = 约 1250 次运算。
# 但我们只要前 32 个输出。twist 的第 i 项只用到 mt[i]、mt[i+1]、mt[i+397]，
# 所以 i < 32 时只需要 mt[0..32] 和 mt[397..428] —— 播种只要跑到 428，twist 只要 32 次。
#
#     1250 次  →  461 次，约 2.7 倍。
#
# 为什么要让你看到这个：**攻击者的速度不是物理常数，是工程量。**
# 每个这种优化都在缩短第 13 课里那个「反应窗口」。
# ---------------------------------------------------------------------------

def first_bytes_high8(seed, n=32):
    """等价于 MT19937(seed).bytes_high8(n)，但只算必要的那部分。"""
    need = n + 1
    top = M + need                      # 397 + n + 1
    mt = [0] * top
    mt[0] = seed & 0xFFFFFFFF
    for i in range(1, top):
        prev = mt[i - 1]
        mt[i] = (1812433253 * (prev ^ (prev >> 30)) + i) & 0xFFFFFFFF
    out = bytearray(n)
    for i in range(n):
        y = (mt[i] & UPPER_MASK) | (mt[i + 1] & LOWER_MASK)
        y = mt[i + M] ^ (y >> 1) ^ (MATRIX_A if y & 1 else 0)
        y ^= y >> 11
        y = (y ^ ((y << 7) & 0x9D2C5680)) & 0xFFFFFFFF
        y = (y ^ ((y << 15) & 0xEFC60000)) & 0xFFFFFFFF
        y ^= y >> 18
        out[i] = y >> 24
    return bytes(out)
