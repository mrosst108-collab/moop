#include <stdio.h>
#include <string.h>
#include "actor.h"
#include "encode.h"
#include "gates.h"
#include "proto.h"
#include "lexer.h"
#include "logic.h"
#include "parser.h"
#include "ram.h"
#include "tapeloop.h"

static int failures;

static void check(bool ok, const char *desc)
{
    printf("%s - %s\n", ok ? "ok  " : "FAIL", desc);
    if (!ok)
        failures = 1;
}

static void test_ccnot_truth_table(void)
{
    /* target flips iff both controls are set */
    for (int c1 = 0; c1 <= 1; c1++)
        for (int c2 = 0; c2 <= 1; c2++)
            for (int t = 0; t <= 1; t++) {
                bool target = t;
                moop_ccnot(c1, c2, &target);
                bool expected = t ^ (c1 && c2);
                check(target == expected, "ccnot truth table entry");
            }
}

static void test_counter_rotation(void)
{
    bool a[5] = {0}, b[3] = {0}, ma[5], mb[3];
    MoopCore core;
    moop_core_init(&core, a, ma, 5, b, mb, 3);
    moop_core_step(&core);
    check(core.a.head == 1, "loop A rotates forward");
    check(core.b.head == 2, "loop B rotates backward");
}

static void test_gate_computes(void)
{
    /* both heads on 1-cells: the gate must flip the next cell of BOTH
     * loops — no loop is a read-only program tape (homoiconicity) */
    bool a[4] = {1, 0, 1, 0}, b[3] = {1, 1, 0}, ma[4], mb[3];
    MoopCore core;
    moop_core_init(&core, a, ma, 4, b, mb, 3);
    moop_core_step(&core);
    check(a[1] == 1, "firing flips loop A's next cell");
    check(b[2] == 1, "firing flips loop B's next cell too (code rewrites code)");
    check(ma[0] && mb[0] && ma[1] && mb[2],
          "a firing marks controls and both targets causal");
    check(!ma[2] && !mb[1], "bystander cells stay causally unmarked");
}

static void test_reversibility(void)
{
    /* coprime lengths so every cell alignment occurs before repeating */
    bool a[5]  = {1, 0, 1, 1, 0};
    bool b[7]  = {0, 1, 1, 0, 1, 0, 1};
    bool ma[5], mb[7];
    bool a0[5], b0[7];
    memcpy(a0, a, sizeof a);
    memcpy(b0, b, sizeof b);

    MoopCore core;
    moop_core_init(&core, a, ma, 5, b, mb, 7);

    enum { TICKS = 35 }; /* one full lcm(5,7) alignment cycle */
    for (int i = 0; i < TICKS; i++)
        moop_core_step(&core);
    check(memcmp(a0, a, sizeof a) != 0, "stepping transforms loop A");
    check(memcmp(b0, b, sizeof b) != 0, "stepping transforms loop B");

    for (int i = 0; i < TICKS; i++)
        moop_core_step_back(&core);
    check(memcmp(a0, a, sizeof a) == 0 &&
          memcmp(b0, b, sizeof b) == 0 &&
          core.a.head == 0 && core.b.head == 0,
          "step_back exactly inverts step over a full cycle");
}

static void test_reversible_gates(void)
{
    bool x = true, y = false;

    moop_not(&x);
    check(x == false, "not flips");
    moop_not(&x);
    check(x == true, "not is self-inverse");

    moop_cnot(true, &y);
    check(y == true, "cnot flips target when control set");
    moop_cnot(false, &y);
    check(y == true, "cnot leaves target when control clear");
    moop_cnot(true, &y);
    check(y == false, "cnot is self-inverse");

    x = true; y = false;
    moop_swap(&x, &y);
    check(x == false && y == true, "swap exchanges");
    moop_swap(&x, &y);
    check(x == true && y == false, "swap is self-inverse");
}

static void test_irreversible_logic(void)
{
    check(moop_and(1, 1) && !moop_and(1, 0), "and");
    check(moop_or(0, 1) && !moop_or(0, 0), "or");
    check(moop_nand(1, 0) && !moop_nand(1, 1), "nand");
    check(moop_nor(0, 0) && !moop_nor(0, 1), "nor");
    check(moop_xor(1, 0) && !moop_xor(1, 1), "xor");
}

static void test_maybe(void)
{
    bool a[5] = {1, 0, 1, 1, 0}, b[7] = {0, 1, 1, 0, 1, 0, 1};
    bool ma[5], mb[7], ma2[5], mb2[7];
    bool a2[5], b2[7];
    memcpy(a2, a, sizeof a);
    memcpy(b2, b, sizeof b);

    enum { DRAWS = 12 };
    bool first[DRAWS], second[DRAWS];
    MoopCore core, core2;

    moop_core_init(&core, a, ma, 5, b, mb, 7);
    for (int i = 0; i < DRAWS; i++)
        first[i] = moop_maybe(&core);

    moop_core_init(&core2, a2, ma2, 5, b2, mb2, 7);
    for (int i = 0; i < DRAWS; i++)
        second[i] = moop_maybe(&core2);
    check(memcmp(first, second, sizeof first) == 0,
          "maybe is deterministic for identical tapes");

    for (int i = 0; i < DRAWS; i++)
        moop_core_step_back(&core);
    check(a[0] == 1 && a[1] == 0 && a[2] == 1 && a[3] == 1 && a[4] == 0 &&
          core.a.head == 0 && core.b.head == 0,
          "maybe's effect on system memory is fully reversible");
}

static void test_causal_pruning(void)
{
    /* one firing, then prune: the causal web survives, inert bits go */
    bool a[4] = {1, 0, 1, 0}, b[3] = {1, 0, 0}, ma[4], mb[3];
    MoopCore core;
    moop_core_init(&core, a, ma, 4, b, mb, 3);
    moop_core_step(&core); /* fires: controls a[0], b[0]; targets a[1], b[2] */
    size_t discarded = moop_core_prune(&core);
    check(a[0] == 1 && a[1] == 1 && b[0] == 1 && b[2] == 1,
          "pruning preserves the causal web");
    check(a[2] == 0, "pruning zeroes causally inert cells");
    check(discarded == 1, "prune reports discarded set bits");
    check(core.ticks == 0 && !ma[0] && !mb[0],
          "prune starts a fresh causal epoch");
}

static void test_auto_prune_epoch(void)
{
    /* all-zero B: the gate never fires, so after one full alignment
     * cycle nothing on A is causally connected to anything — the whole
     * tape is prunable and the machine returns to a blank rotor */
    bool a[5] = {1, 1, 0, 1, 0}, b[7] = {0}, ma[5], mb[7];
    MoopCore core;
    moop_core_init(&core, a, ma, 5, b, mb, 7);
    check(moop_core_epoch(&core) == 35, "epoch is lcm(len_a, len_b)");
    size_t discarded = moop_core_run(&core, 35);
    check(discarded == 3, "run auto-prunes at the epoch boundary");
    bool blank = true;
    for (int i = 0; i < 5; i++)
        blank = blank && !a[i];
    check(blank, "causally disconnected information is fully pruned");
}

static void test_ram(void)
{
    uint8_t bytes[16] = {0};
    MoopRam ram;
    moop_ram_init(&ram, bytes, sizeof bytes);
    moop_ram_write(&ram, 3, 0xAB);
    check(moop_ram_read(&ram, 3) == 0xAB, "ram write/read round-trip");
    moop_ram_write(&ram, 3, 0xCD);
    check(moop_ram_read(&ram, 3) == 0xCD, "ram overwrites (forgets) freely");
}

static bool msg_maybe(MoopActor *self)
{
    return moop_maybe(&self->core);
}

static bool msg_ping(MoopActor *self)
{
    (void)self;
    return true;
}

static void test_actor(void)
{
    bool a[5] = {1, 0, 1, 1, 0}, b[7] = {0, 1, 1, 0, 1, 0, 1};
    bool a0[5], b0[7], ma[5], mb[7];
    memcpy(a0, a, sizeof a);
    memcpy(b0, b, sizeof b);

    MoopMessage table[4];
    MoopActor actor;
    moop_actor_init(&actor, a, ma, 5, b, mb, 7, table, 4);

    bool reply = false;
    check(!moop_actor_send(&actor, "ping", &reply),
          "an unhosted message is a miss");
    check(moop_actor_host(&actor, "ping", msg_ping) &&
          moop_actor_send(&actor, "ping", &reply) && reply,
          "a hosted message answers");

    check(!moop_actor_send(&actor, "parent", &reply),
          "lookup never delegates: actors are non-hereditary");

    /* the body inherits reversibility from the substrate: undo the
     * reversible effects of every observation and the actor's entire
     * state is back — replies were the only irreversible product */
    moop_actor_host(&actor, "maybe", msg_maybe);
    enum { DRAWS = 9 };
    for (int i = 0; i < DRAWS; i++)
        moop_actor_send(&actor, "maybe", &reply);
    for (int i = 0; i < DRAWS; i++)
        moop_core_step_back(&actor.core);
    check(memcmp(a0, a, sizeof a) == 0 && memcmp(b0, b, sizeof b) == 0 &&
          actor.core.a.head == 0 && actor.core.b.head == 0,
          "actor bodies inherit reversibility from the substrate");
}

static void test_encoding(void)
{
    bool a[8] = {0}, b[13] = {0}, ma[8], mb[13];
    MoopCore core;
    moop_core_init(&core, a, ma, 8, b, mb, 13);

    check(moop_encode_max(&core) == 255, "an 8-cell loop carries 0..255");
    moop_encode_xor(&core, 5);
    check(moop_decode(&core) == 5, "decode reads back what encode wrote");
    check(a[0] && !a[1] && a[2], "bit i of the value is cell i of loop A");
    check(ma[0] && ma[2] && !ma[1],
          "deliberate deposits are causally marked (pruning spares them)");
    moop_encode_xor(&core, 5);
    check(moop_decode(&core) == 0, "encoding is self-inverse");

    bool xa[8] = {0}, xb[13] = {0}, mxa[8], mxb[13];
    MoopCore other;
    moop_core_init(&other, xa, mxa, 8, xb, mxb, 13);
    moop_encode_xor(&core, 9);
    moop_encode_xor(&other, 3);
    moop_exchange(&core, &other);
    check(moop_decode(&core) == 3 && moop_decode(&other) == 9,
          "exchange moves values both ways");
    moop_exchange(&core, &other);
    check(moop_decode(&core) == 9 && moop_decode(&other) == 3,
          "exchange is self-inverse");
}

static bool msg_observe(MoopProto *self)
{
    /* answers from the receiver's own body: proves self stays the
     * receiver even when the handler is found on an ancestor */
    return self->core.a.cells[0];
}

static void test_proto_generation(void)
{
    bool aa[5] = {1, 0, 1, 1, 0}, ab[7] = {0, 1, 1, 0, 1, 0, 1};
    bool maa[5], mab[7];
    MoopMessage atable[2];
    MoopActor actor;
    moop_actor_init(&actor, aa, maa, 5, ab, mab, 7, atable, 2);

    bool sa[4], sb[5], msa[4], msb[5];
    bool ua[4], ub[5], mua[4], mub[5];
    bool pa[4], pb[5], mpa[4], mpb[5];
    MoopProtoMessage stable[2], utable[2], ptable[2];
    MoopProto sysroot, uroot, proto;

    /* actor -> system root -> user root -> proto */
    moop_actor_generate_root(&actor, &sysroot, sa, msa, 4, sb, msb, 5,
                             stable, 2);
    moop_proto_generate(&sysroot, &uroot, ua, mua, 4, ub, mub, 5,
                        utable, 2);
    moop_proto_generate(&uroot, &proto, pa, mpa, 4, pb, mpb, 5,
                        ptable, 2);

    check(sysroot.facing == MOOP_FACING_SYSTEM && sysroot.parent == NULL,
          "the actor generates the system-facing root");
    check(uroot.facing == MOOP_FACING_USER && uroot.parent == NULL,
          "the system root generates user-facing roots with no parent");
    check(proto.facing == MOOP_FACING_USER && proto.parent == &uroot,
          "user-facing protos generate hereditary children");

    /* delegation is hereditary among user protos, self = receiver */
    bool reply = false;
    moop_proto_host(&uroot, "observe", msg_observe);
    check(moop_proto_send(&proto, "observe", &reply) && reply == pa[0],
          "lookup delegates to the parent; self stays the receiver");

    /* ...but never crosses the layer boundary */
    moop_proto_host(&sysroot, "system", msg_observe);
    check(!moop_proto_send(&uroot, "system", &reply),
          "delegation never crosses into the system-facing root");

    /* every generated body inherits reversibility from the substrate */
    bool pa0[4], pb0[5];
    memcpy(pa0, pa, sizeof pa0);
    memcpy(pb0, pb, sizeof pb0);
    for (int i = 0; i < 11; i++)
        moop_core_step(&proto.core);
    for (int i = 0; i < 11; i++)
        moop_core_step_back(&proto.core);
    check(memcmp(pa0, pa, sizeof pa0) == 0 &&
          memcmp(pb0, pb, sizeof pb0) == 0,
          "generated protos inherit reversibility");

    /* generation itself is reversible for the generator: undo the
     * seeding draws and the actor is back before the birth */
    for (int i = 0; i < 4 + 5; i++)
        moop_core_step_back(&actor.core); /* undo sysroot's 9 seed draws */
    bool aa0[5] = {1, 0, 1, 1, 0}, ab0[7] = {0, 1, 1, 0, 1, 0, 1};
    check(memcmp(aa, aa0, sizeof aa0) == 0 &&
          memcmp(ab, ab0, sizeof ab0) == 0 &&
          actor.core.a.head == 0 && actor.core.b.head == 0,
          "generating costs the generator nothing irreversible");
}

static void test_lexer(void)
{
    MoopLexer lx;
    moop_lexer_init(&lx, "reply is greeting -> alice <- bob <-> carol 42");
    static const MoopTokKind expect[] = {
        MOOP_TOK_WORD, MOOP_TOK_IS, MOOP_TOK_WORD, MOOP_TOK_SEND,
        MOOP_TOK_WORD, MOOP_TOK_INHERIT, MOOP_TOK_WORD, MOOP_TOK_BIJECT,
        MOOP_TOK_WORD, MOOP_TOK_NUMBER, MOOP_TOK_END,
    };
    bool ok = true;
    for (size_t i = 0; i < sizeof expect / sizeof expect[0]; i++) {
        MoopToken t = moop_lexer_next(&lx);
        ok = ok && t.kind == expect[i];
    }
    check(ok, "lexer tokenizes all four operators, words and numbers");

    moop_lexer_init(&lx, "island isnt");
    MoopToken t = moop_lexer_next(&lx);
    check(t.kind == MOOP_TOK_WORD && t.len == 6,
          "'is' prefix does not hijack longer words");
    t = moop_lexer_next(&lx);
    check(t.kind == MOOP_TOK_WORD && t.len == 4, "isnt is a word");

    moop_lexer_init(&lx, "a <-> b");
    moop_lexer_next(&lx);
    t = moop_lexer_next(&lx);
    check(t.kind == MOOP_TOK_BIJECT && t.len == 3,
          "<-> lexes as one bijective token, not <- then >");

    moop_lexer_init(&lx, "a @ b");
    moop_lexer_next(&lx);
    t = moop_lexer_next(&lx);
    check(t.kind == MOOP_TOK_ERROR && t.start[0] == '@',
          "unexpected characters become error tokens");

    /* word spellings are the same tokens as the arrows */
    moop_lexer_init(&lx, "rex inherits dog mirrors box ask maybe");
    static const MoopTokKind words[] = {
        MOOP_TOK_WORD, MOOP_TOK_INHERIT, MOOP_TOK_WORD, MOOP_TOK_BIJECT,
        MOOP_TOK_WORD, MOOP_TOK_SEND, MOOP_TOK_WORD, MOOP_TOK_END,
    };
    bool same = true;
    for (size_t i = 0; i < sizeof words / sizeof words[0]; i++)
        same = same && moop_lexer_next(&lx).kind == words[i];
    check(same, "ask/inherits/mirrors lex as the arrow tokens");

    moop_lexer_init(&lx, "asked mirrorsmith");
    t = moop_lexer_next(&lx);
    check(t.kind == MOOP_TOK_WORD && t.len == 5,
          "reserved words do not hijack longer words");
}

static void test_parser(void)
{
    MoopAst ast;
    char err[64];

    check(moop_parse("x is p -> q -> r", &ast, err, sizeof err),
          "a definition of a pipeline parses");
    const MoopNode *root = &ast.nodes[ast.root];
    bool shape = root->kind == MOOP_NODE_IS &&
                 ast.nodes[root->right].kind == MOOP_NODE_SEND &&
                 ast.nodes[ast.nodes[root->right].left].kind ==
                     MOOP_NODE_SEND;
    check(shape, "pipelines associate left");
    check(root->len == 1 && root->start[0] == 'x',
          "the definition carries its name");

    check(moop_parse("42", &ast, err, sizeof err) &&
              ast.nodes[ast.root].kind == MOOP_NODE_NUMBER,
          "a bare number parses");
    check(moop_parse("p <-> q", &ast, err, sizeof err) &&
              ast.nodes[ast.root].kind == MOOP_NODE_BIJECT,
          "a bijection parses");

    check(moop_parse("dog ask speak is ask maybe", &ast, err, sizeof err),
          "a message definition parses");
    root = &ast.nodes[ast.root];
    check(root->kind == MOOP_NODE_IS &&
              ast.nodes[root->left].kind == MOOP_NODE_SEND &&
              ast.nodes[root->right].kind == MOOP_NODE_SEND,
          "a message definition is designator + stored chain");

    check(moop_parse("ask maybe", &ast, err, sizeof err) &&
              ast.nodes[ast.root].kind == MOOP_NODE_SEND &&
              ast.nodes[ast.nodes[ast.root].left].kind ==
                  MOOP_NODE_RECEIVER,
          "a headless chain gets the receiver as its head");

    check(moop_parse("rex is a dog", &ast, err, sizeof err) &&
              ast.nodes[ast.root].kind == MOOP_NODE_IS &&
              ast.nodes[ast.nodes[ast.root].right].kind == MOOP_NODE_BIRTH,
          "the article parses as a birth");
    check(!moop_parse("a ask maybe", &ast, err, sizeof err),
          "the article must be followed by a name");

    check(moop_parse("dog ask mood is", &ast, err, sizeof err) &&
              ast.nodes[ast.root].kind == MOOP_NODE_IS &&
              ast.nodes[ast.root].right == -1,
          "a trailing is announces an indented block");

    check(!moop_parse("5 is x", &ast, err, sizeof err),
          "only names and messages can be defined");
    check(!moop_parse("p <- q is 1", &ast, err, sizeof err),
          "inheritance is not a designator");
    check(!moop_parse("p -> -> q", &ast, err, sizeof err),
          "operators need operands");
    check(!moop_parse("p q", &ast, err, sizeof err),
          "adjacent terms need an operator");
}

int main(void)
{
    test_lexer();
    test_parser();
    test_ccnot_truth_table();
    test_reversible_gates();
    test_counter_rotation();
    test_gate_computes();
    test_reversibility();
    test_causal_pruning();
    test_auto_prune_epoch();
    test_irreversible_logic();
    test_maybe();
    test_ram();
    test_encoding();
    test_actor();
    test_proto_generation();
    return failures;
}
