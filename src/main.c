#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "eval.h"
#include "moop.h"
#include "parser.h"

/* Entry point for the moop interpreter.
 * The pipeline is lex -> parse -> eval; whatever a stage cannot do yet
 * is reported honestly (bijections, reflection) — nothing pretends to
 * work.
 *
 * One reader serves both the REPL and a file. A file is a session
 * without the banner and the prompts: the same lines mean the same
 * thing in both, and a statement that is not a definition prints its
 * value. They differ in two places only. The REPL reports an error and goes on; a file stops
 * at its first error, which is named by line, and the exit status is 1.
 * And `quit` belongs to the REPL: it is a command, not a word of the
 * language, so in a file it is a name like any other.
 *
 * Comments are full lines (docs/foundations.md, F1-F3): a line whose
 * first character other than a space or a tab is `;` is set aside before
 * indentation and blocks are considered. It runs nothing and prints
 * nothing, it neither opens nor closes a block, and its indentation is
 * never an error. A blank line still closes a block, so the two kinds of
 * line that run nothing differ on purpose. A `;` after code is not a
 * comment: the lexer refuses it as a stray character. */

typedef struct {
    FILE *in;
    const char *name;    /* the file's path; NULL for the REPL */
    unsigned long line;  /* number of the line last read */
    bool failed;         /* an error was reported */
} Reader;

static void report(Reader *r, unsigned long line, const char *msg)
{
    fflush(stdout); /* what was printed before the error comes before it */
    if (r->name != NULL)
        fprintf(stderr, "%s:%lu: error: %s\n", r->name, line, msg);
    else
        fprintf(stderr, "error: %s\n", msg);
    r->failed = true;
}

/* A file stops at its first error; the REPL carries on. */
static bool stopped(const Reader *r)
{
    return r->name != NULL && r->failed;
}

typedef enum { LINE_OK, LINE_END, LINE_BAD } LineStatus;

/* Read one line without its ending (LF or CRLF). A line that does not
 * fit, or that holds a NUL byte, is read to its end and refused whole:
 * it is never cut into pieces that would run as something else. */
static LineStatus read_line(Reader *r, const char *prompt,
                            char *buf, size_t cap)
{
    if (r->name == NULL) {
        printf("%s", prompt);
        fflush(stdout);
    }

    size_t n = 0;
    bool too_long = false, nul = false;
    int c;
    while ((c = getc(r->in)) != EOF && c != '\n') {
        if (c == '\0')
            nul = true;
        if (n + 1 < cap)
            buf[n++] = (char)c;
        else
            too_long = true;
    }
    if (c == EOF && ferror(r->in)) {
        fflush(stdout);
        if (r->name != NULL)
            fprintf(stderr, "error: cannot read %s: %s\n", r->name,
                    strerror(errno));
        else
            fprintf(stderr, "error: cannot read the input\n");
        r->failed = true;
        return LINE_END;
    }
    if (c == EOF && n == 0 && !too_long)
        return LINE_END;

    r->line++;
    if (n > 0 && buf[n - 1] == '\r')
        n--;
    buf[n] = '\0';
    if (too_long) {
        report(r, r->line, "line too long");
        return LINE_BAD;
    }
    if (nul) {
        report(r, r->line, "a NUL byte in the line");
        return LINE_BAD;
    }
    return LINE_OK;
}

static bool is_blank(const char *line)
{
    return line[strspn(line, " \t")] == '\0';
}

/* A full-line comment. It is recognized only after the line has been
 * read, so the reader's refusals (a line too long, a NUL byte) apply to
 * comments as to everything else. */
static bool is_comment(const char *line)
{
    return line[strspn(line, " \t")] == ';';
}

static void print_value(const MoopValue *v)
{
    switch (v->kind) {
    case MOOP_VAL_NUMBER: {
        /* canonical: reads back as an equal number (F8) */
        char text[MOOP_NUMBER_TEXT_MAX];
        moop_number_text(v->number, text, sizeof text);
        printf("%s\n", text);
        break;
    }
    case MOOP_VAL_BOOL:   printf(v->truth ? "true\n" : "false\n"); break;
    case MOOP_VAL_PROTO:  printf("a proto\n");                     break;
    }
}

/* An `is` at the end of a line opens an indented block: the body
 * follows one chain per line and a blank line (or the end of the
 * input) closes it. */
static void collect_block(Reader *r, const MoopAst *head_src)
{
    char line[1024];
    char err[MOOP_ERR_MAX];
    MoopAst *bodies[16];
    unsigned long body_line[16];    /* where each body line was read */
    size_t n = 0;
    unsigned long opened = r->line; /* the line that opened the block */

    /* the head's lexemes live in the caller's line buffer, which the
     * loop below reuses — take an owned copy first */
    MoopAst *head = moop_ast_clone(head_src);
    if (head == NULL) {
        report(r, opened, "out of memory");
        return;
    }

    for (;;) {
        LineStatus st = read_line(r, "....> ", line, sizeof line);
        if (st == LINE_BAD)
            goto out;
        if (st == LINE_END) {
            if (ferror(r->in))
                goto out; /* the input could not be read */
            break;
        }
        if (is_comment(line))
            continue; /* the block stays open, indented or not */
        if (is_blank(line))
            break; /* blank line closes the block */
        if (line[0] != ' ' && line[0] != '\t') {
            report(r, r->line,
                   "expected an indented line or a blank line");
            goto out;
        }
        if (n == sizeof bodies / sizeof bodies[0]) {
            report(r, r->line, "the definition body is too long");
            goto out;
        }

        MoopAst ast;
        if (!moop_parse(line, &ast, err, sizeof err)) {
            report(r, r->line, err);
            goto out;
        }
        if (ast.nodes[ast.root].kind == MOOP_NODE_IS) {
            report(r, r->line, "definitions cannot nest (yet)");
            goto out;
        }
        bodies[n] = moop_ast_clone(&ast);
        if (bodies[n] == NULL) {
            report(r, r->line, "out of memory");
            goto out;
        }
        body_line[n] = r->line;
        n++;
    }

    if (n == 0) {
        report(r, opened, "the definition body is empty");
        goto out;
    }
    /* a block is evaluated when it closes; what goes wrong then is
     * reported at the body line that failed, as it was read (comment
     * lines may stand between body lines), or at the opening line */
    size_t at;
    if (!moop_eval_block(head, bodies, n, &at, err, sizeof err))
        report(r, at < n ? body_line[at] : opened, err);
    moop_ast_free(head);
    return;

out:
    while (n > 0)
        moop_ast_free(bodies[--n]);
    moop_ast_free(head);
}

static void interpret(Reader *r, const char *line)
{
    MoopAst ast;
    MoopValue value;
    bool quiet = false;
    char err[MOOP_ERR_MAX];

    if (!moop_parse(line, &ast, err, sizeof err)) {
        report(r, r->line, err);
        return;
    }
    const MoopNode *root = &ast.nodes[ast.root];
    if (root->kind == MOOP_NODE_IS && root->right == -1) {
        collect_block(r, &ast);
        return;
    }
    if (!moop_eval(&ast, &value, &quiet, err, sizeof err)) {
        report(r, r->line, err);
        return;
    }
    if (!quiet)
        print_value(&value);
}

/* The session: statements until the input ends. */
static void session(Reader *r)
{
    char line[1024];
    while (!stopped(r)) {
        LineStatus st = read_line(r, "moop> ", line, sizeof line);
        if (st == LINE_END)
            break;
        if (st == LINE_BAD)
            continue;
        if (r->name == NULL && strcmp(line, "quit") == 0)
            break;
        if (is_comment(line) || is_blank(line))
            continue;
        /* Indentation says a line belongs to a block. The REPL's prompt
         * shows whether one is open; a file has no prompt, so a line
         * indented under nothing is refused, not run as if it were
         * flush left. */
        if (line[0] == ' ' || line[0] == '\t') {
            report(r, r->line,
                   "an indented line belongs to a block, and none is open");
            continue;
        }
        interpret(r, line);
    }
}

static int run_file(const char *path)
{
    FILE *in = fopen(path, "r");
    if (in == NULL) {
        fprintf(stderr, "error: cannot open %s: %s\n", path,
                strerror(errno));
        return 1;
    }
    Reader r = { .in = in, .name = path };
    moop_eval_init();
    session(&r);
    fclose(in);
    return r.failed ? 1 : 0;
}

int main(int argc, char **argv)
{
    if (argc > 1) {
        if (strcmp(argv[1], "--version") == 0) {
            printf("moop %s\n", MOOP_VERSION);
            return 0;
        }
        if (argc > 2) {
            fprintf(stderr, "error: moop runs one file\n");
            return 1;
        }
        if (argv[1][0] == '-') {
            fprintf(stderr, "error: unknown option %s\n", argv[1]);
            return 1;
        }
        return run_file(argv[1]);
    }
    Reader r = { .in = stdin, .name = NULL };
    moop_eval_init();
    printf("moop %s\n", MOOP_VERSION);
    printf("type \"quit\" to leave\n");
    session(&r);
    return 0;
}
