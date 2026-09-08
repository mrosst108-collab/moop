/* Fixed-input behavioral probe: compiles against any commit's cJSON.c.
 * Uses only the oldest API: cJSON_Parse, cJSON_Print, cJSON_Delete. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cJSON.h"
static void probe(const char *name, const char *in)
{
    cJSON *j = cJSON_Parse(in);
    if (!j) { printf("%s: REJECT\n", name); return; }
    char *out = cJSON_Print(j);
    printf("%s: %s\n", name, out ? out : "(null)");
    free(out); cJSON_Delete(j);
}
int main(void)
{
    probe("num", "[1.5, 3.14159265358979323846, 1e300, 0.1, 100000000000000000000]");
    probe("str", "[\"a\\u00e9b\", \"tab\\tnl\\n\", \"\\ud83d\\ude00\"]");
    probe("obj", "{\"a\":{\"b\":[true,false,null]},\"c\":\"\"}");
    static char deep[4096]; size_t i;
    for (i = 0; i < 999; i++) deep[i] = '['; deep[i++] = '1'; for (size_t k = 0; k < 999; k++) deep[i++] = ']'; deep[i] = 0;
    cJSON *d = cJSON_Parse(deep); printf("depth999: %s\n", d ? "ACCEPT" : "REJECT"); cJSON_Delete(d);
    i = 0; for (; i < 1001; i++) deep[i] = '['; deep[i++] = '1'; for (size_t k = 0; k < 1001; k++) deep[i++] = ']'; deep[i] = 0;
    d = cJSON_Parse(deep); printf("depth1001: %s\n", d ? "ACCEPT" : "REJECT"); cJSON_Delete(d);
    probe("trail", "[1,2,]");
    probe("dup", "{\"k\":1,\"k\":2}");
    return 0;
}
