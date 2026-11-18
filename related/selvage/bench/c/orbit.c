#include <stdint.h>
#include <stdio.h>
typedef struct { int64_t q, p; } phase;
static phase orbit(int64_t k, int64_t steps, phase s) {
    for (int64_t i = 0; i < steps; i++) { s.p -= k * s.q / 2000; s.q += s.p; s.p -= k * s.q / 2000; }
    return s;
}
static phase orbit_inv(int64_t k, int64_t steps, phase s) {
    for (int64_t i = 0; i < steps; i++) { s.p += k * s.q / 2000; s.q -= s.p; s.p += k * s.q / 2000; }
    return s;
}
int main(void) {
    phase s = orbit(10, 100000000, (phase){100000, 0});
    printf("Phase(%lld, %lld)\n", (long long)s.q, (long long)s.p);
    phase b = orbit_inv(10, 100000000, s);
    printf("Phase(%lld, %lld)\n", (long long)b.q, (long long)b.p);
    return 0;
}
