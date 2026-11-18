#include <stdint.h>
#include <stdio.h>
typedef struct { int64_t q, p; } phase;
int main(void) {
    phase s = {100000000, 0};
    for (int64_t b = 0; b < 100000; b++)
        for (int i = 0; i < 1000; i++) {
            s.p -= 10 * s.q / 2000; s.q += s.p; s.p -= 10 * s.q / 2000;
            s.p = s.p - s.p / 4096;
        }
    printf("Phase(%lld, %lld)\n", (long long)s.q, (long long)s.p);
    return 0;
}
