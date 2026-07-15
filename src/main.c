#include <stdio.h>
#include <string.h>
#include "lexer.h"
#include "moop.h"

/* Entry point for the moop interpreter.
 * Input is lexed for real; the parser and evaluator do not exist yet, so
 * beyond lex errors the REPL reports that evaluation is unimplemented —
 * nothing pretends to work. */

static bool lex_line(const char *line)
{
    MoopLexer lx;
    moop_lexer_init(&lx, line);
    for (;;) {
        MoopToken t = moop_lexer_next(&lx);
        if (t.kind == MOOP_TOK_ERROR) {
            fprintf(stderr, "error: unexpected character '%.*s'\n",
                    (int)t.len, t.start);
            return false;
        }
        if (t.kind == MOOP_TOK_END)
            return true;
    }
}

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
        if (line[0] != '\0' && lex_line(line))
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
