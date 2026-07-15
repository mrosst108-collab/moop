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

/* An `is` at the end of a line opens an indented block: the body
 * follows one chain per line and a blank line (or EOF) closes it. */
static void collect_block(const MoopAst *head_src)
{
    char line[1024];
    char err[128];
    MoopAst *bodies[16];
    size_t n = 0;

    /* the head's lexemes live in the caller's line buffer, which the
     * loop below reuses — take an owned copy first */
    MoopAst *head = moop_ast_clone(head_src);
    if (head == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return;
    }

    for (;;) {
        printf("....> ");
        fflush(stdout);
        if (!fgets(line, sizeof line, stdin))
            break;
        line[strcspn(line, "\n")] = '\0';
        if (line[strspn(line, " \t")] == '\0')
            break; /* blank line closes the block */
        if (line[0] != ' ' && line[0] != '\t') {
            fprintf(stderr,
                    "error: expected an indented line or a blank line\n");
            goto out;
        }
        if (n == sizeof bodies / sizeof bodies[0]) {
            fprintf(stderr, "error: the definition body is too long\n");
            goto out;
        }

        MoopAst ast;
        const char *stmt = line + strspn(line, " \t");
        if (!moop_parse(stmt, &ast, err, sizeof err)) {
            fprintf(stderr, "error: %s\n", err);
            goto out;
        }
        if (ast.nodes[ast.root].kind == MOOP_NODE_IS) {
            fprintf(stderr, "error: definitions cannot nest (yet)\n");
            goto out;
        }
        bodies[n] = moop_ast_clone(&ast);
        if (bodies[n] == NULL) {
            fprintf(stderr, "error: out of memory\n");
            goto out;
        }
        n++;
    }

    if (n == 0) {
        fprintf(stderr, "error: the definition body is empty\n");
        goto out;
    }
    if (!moop_eval_block(head, bodies, n, err, sizeof err))
        fprintf(stderr, "error: %s\n", err);
    moop_ast_free(head);
    return;

out:
    while (n > 0)
        moop_ast_free(bodies[--n]);
    moop_ast_free(head);
}

static void interpret(const char *line)
{
    MoopAst ast;
    MoopValue value;
    bool quiet = false;
    char err[128];

    if (!moop_parse(line, &ast, err, sizeof err)) {
        fprintf(stderr, "error: %s\n", err);
        return;
    }
    const MoopNode *root = &ast.nodes[ast.root];
    if (root->kind == MOOP_NODE_IS && root->right == -1) {
        collect_block(&ast);
        return;
    }
    if (!moop_eval(&ast, &value, &quiet, err, sizeof err)) {
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
