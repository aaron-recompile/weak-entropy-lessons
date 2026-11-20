#!/bin/sh
# 把全部课程跑一遍，确认每一课都真的能跑出结果。
#   ./run_all.sh          正常跑
#   ./run_all.sh -q       只报通过/失败
set -e
cd "$(dirname "$0")"
QUIET=""
[ "$1" = "-q" ] && QUIET=1

PY_LESSONS="
lessons/common/bip39.py
lessons/common/btc.py
lessons/01_recompute/recompute.py
lessons/02_milk_sad/milk_sad.py
lessons/03_ill_bloom/ill_bloom.py
lessons/04_trust_wallet_wasm/trust_wallet.py
lessons/05_cake_wallet/cake_wallet.py
lessons/06_php_mt_rand/php_mt_rand.py
lessons/07_brainwallet/brainwallet.py
lessons/08_coldcard_link/enumerate_mk3.py
lessons/09_xor/xor_entropy.py
lessons/10_pbkdf2/pbkdf2_wont_save_you.py
lessons/11_five_guards/five_guards.py
lessons/12_attribution/attribution.py
lessons/13_attacker_tempo/tempo.py
lessons/14_prediction/prediction.py
"
fail=0
for f in $PY_LESSONS; do
    printf "%-48s " "$f"
    start=$(date +%s)
    if [ -n "$QUIET" ]; then
        if python3 "$f" > /dev/null 2>&1; then echo "✅ $(( $(date +%s) - start ))s"; else echo "❌"; fail=1; fi
    else
        echo ""
        python3 "$f" || fail=1
    fi
done

printf "%-48s " "lessons/08_coldcard_link (make all)"
if [ -n "$QUIET" ]; then
    if ( cd lessons/08_coldcard_link && make -s all >/dev/null 2>&1 ); then echo "✅"; else echo "❌"; fail=1; fi
else
    echo ""; ( cd lessons/08_coldcard_link && make -s all ) || fail=1
fi

printf "%-48s " "lessons/14_prediction (嗅探器回归)"
if ( cd lessons/14_prediction && python3 audit_wallet_code.py samples/good_stdlib.py 2>&1 | grep -q "没有命中" \
     && python3 audit_wallet_code.py samples/bad_cake_wallet.py 2>&1 | grep -q "R3" ); then echo "✅"; else echo "❌"; fail=1; fi

echo ""
[ "$fail" = 0 ] && echo "全部通过。" || { echo "有失败。"; exit 1; }
