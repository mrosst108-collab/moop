#include <stdio.h>
#include <string.h>
#include "eval.h"
#include "moop.h"
#include "parser.h"

/* Entry point for the moop interpreter.
 * The pipeline is lex -> parse -> eval; whatever a stage cannot do yet
 * is reported honestly (bijections, files) — nothing pretends to work. */

static void print_value(const MoopValue *v)
{
    switch (v->kind) {
    case MOOP_VAL_NUMBER: printf("%ld\n", v->number);              break;
    case MOOP_VAL_BOOL:   printf(v->truth ? "true\n" : "false\n"); break;
    case MOOP_VAL_PROTO:  printf("a proto\n");                     break;
    }
}

static void interpret(const char *line)
{
    MoopAst ast;
    MoopValue value;
    bool quiet = false;
    char err[128];

    if (!moop_parse(line, &ast, err, sizeof err) ||
        !moop_eval(&ast, &value, &quiet, err, sizeof err)) {
        fprintf(stderr, "error: %s\n", err);
        return;
    }
    if (!quiet)
        print_value(&value);
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
        if (line[strspn(line, " \t")] != '\0')
            interpret(line);
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
    moop_eval_init();
    repl();
    return 0;
}
