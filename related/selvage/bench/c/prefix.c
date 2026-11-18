#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static void prefix_sum(uint64_t *a, int64_t n) { for (int64_t i = 1; i < n; i++) a[i] += a[i - 1]; }
static void prefix_sum_inv(uint64_t *a, int64_t n) { for (int64_t i = n - 1; i >= 1; i--) a[i] -= a[i - 1]; }
static uint64_t checksum(const uint64_t *a, int64_t n) {
    uint64_t s = 0;
    for (int64_t i = 0; i < n; i++) s = (s * 31) ^ a[i];
    return s;
}
int main(void) {
    int64_t n = 10000000;
    uint64_t *a = malloc(sizeof(uint64_t) * (size_t)n);
    for (int64_t i = 0; i < n; i++) a[i] = (uint64_t)i * 2654435761u;
    for (int r = 0; r < 10; r++) { prefix_sum(a, n); prefix_sum_inv(a, n); }
    printf("%llu\n", (unsigned long long)checksum(a, n));
    prefix_sum(a, n);
    printf("%llu\n", (unsigned long long)checksum(a, n));
    free(a);
    return 0;
}
