#include <stdint.h>
#include <stdio.h>
static uint64_t chain(uint64_t n) {
    uint64_t steps = 0;
    while (n != 1) { n = (n % 2 == 0) ? n / 2 : 3 * n + 1; steps++; }
    return steps;
}
int main(void) {
    uint64_t best = 0, best_start = 1;
    for (uint64_t s = 1; s <= 3000000; s++) {
        uint64_t c = chain(s);
        if (c > best) { best = c; best_start = s; }
    }
    printf("%llu\n", (unsigned long long)best_start);
    return 0;
}
