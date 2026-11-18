#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(void) {
    int64_t n = 50000000, count = 0;
    bool *composite = calloc((size_t)n, sizeof(bool));
    for (int64_t i = 2; i < n; i++) {
        if (!composite[i]) {
            count++;
            for (int64_t j = i * i; j < n; j += i) composite[j] = true;
        }
    }
    printf("%lld\n", (long long)count);
    free(composite);
    return 0;
}
