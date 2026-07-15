#include <stdio.h>
#include <string.h>
#include "moop.h"

/* Entry point for the moop interpreter.
 * The evaluator does not exist yet; the REPL only reads input and
 * reports that evaluation is unimplemented, so nothing pretends to work. */

static void repl(void)
{
    char line[1024];
    printf("moop %s\n", MOOP_VERSION);
    printf("type \"quit\" to leave\n");
    for (;;) {
        printf("moop> ");
        fflush(stdout);
        if (!fgets(line, sizeof line, stdin))
            break;
        line[strcspn(line, "\n")] = '\0';
        if (strcmp(line, "quit") == 0)
            break;
        if (line[0] != '\0')
            fprintf(stderr, "error: evaluation is not implemented yet\n");
    }
}

int main(int argc, char **argv)
{
    if (argc > 1) {
        if (strcmp(argv[1], "--version") == 0) {
            printf("moop %s\n", MOOP_VERSION);
            return 0;
        }
        fprintf(stderr, "error: running files is not implemented yet\n");
        return 1;
    }
    repl();
    return 0;
}
