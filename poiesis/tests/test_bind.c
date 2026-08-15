/* poiesis — GATE 1 suite: transition read-sets (spec §10).
 *
 * The three specified outcomes, and what a failure of each would mean:
 *
 *   C16   fixed arg struct accepted   -- rejecting it prohibits a legitimate
 *                                        realization strategy
 *   C15   undeclared read rejected    -- accepting it permits hidden
 *                                        dependency growth
 *   C15b  corresponding change valid  -- rejecting it freezes the interface
 *                                        at first declaration
 *
 * Reads(T) and ArgType(T) are supplied as two independent declarations in
 * every case below.  No test derives one from the other.
 */
#include "rme/bind.h"

extern void rme_check(bool cond, const char *id, const char *what);

/* ArgType as first declared.  A compile-time-fixed argument struct: C16
 * exists to establish that this is a VALID realization, since
 * HardWiredArgs(T) => !RME7Conforms(T) is a prohibited inference. */
static const RmeField args_v1_fields[] = {
    { "temp",     "double", "temperature" },
    { "pressure", "double", "pressure"    },
};
static const RmeArgType args_v1 = { "StepArgs", args_v1_fields, 2 };

/* The same interface CHANGED CORRESPONDINGLY: one further field, which
 * explicitly represents the newly declared dependency. */
static const RmeField args_v2_fields[] = {
    { "temp",     "double", "temperature" },
    { "pressure", "double", "pressure"    },
    { "humidity", "double", "humidity"    },
};
static const RmeArgType args_v2 = { "StepArgs", args_v2_fields, 3 };

static const RmeRead reads_base[] = {
    { "temperature", "double" },
    { "pressure",    "double" },
};

/* Reads(T) with one dependency added.  Whether this is valid depends
 * entirely on which ArgType it is paired with — which is the point. */
static const RmeRead reads_expanded[] = {
    { "temperature", "double" },
    { "pressure",    "double" },
    { "humidity",    "double" },
};

void rme_test_bind(void);

void rme_test_bind(void)
{
    /* ---- C16: interface unchanged, every declared read represented. */
    {
        RmeTransitionBind t = { "step", &args_v1, reads_base, 2 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(r.ok, "C16",
                  "fixed argument struct with all declared reads represented is valid");
    }

    /* ---- C15: Reads(T) expanded, ArgType(T) unchanged.  The new read has
     * no representing field, so the dependency grew without the interface
     * change that would have made it visible at the boundary. */
    {
        RmeTransitionBind t = { "step", &args_v1, reads_expanded, 3 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(!r.ok && r.read == 2 && r.why != nullptr,
                  "C15",
                  "undeclared read expansion under unchanged ArgType is rejected, naming the read");
    }

    /* ---- C15b: same expanded Reads(T), interface changed to match. */
    {
        RmeTransitionBind t = { "step", &args_v2, reads_expanded, 3 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(r.ok, "C15b",
                  "ArgType changed correspondingly: the expanded read is represented, valid");
    }

    /* ---- B3: a field spelled exactly like the dependency, designating
     * nothing.  Represents() is a DECLARATION, not a spelling coincidence. */
    {
        static const RmeField coincidence[] = {
            { "temperature", "double", nullptr },
            { "pressure",    "double", "pressure" },
        };
        static const RmeArgType at = { "StepArgs", coincidence, 2 };
        RmeTransitionBind t = { "step", &at, reads_base, 2 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(!r.ok && r.read == 0, "B3",
                  "field spelled like the dependency but designating nothing does not represent it");
    }

    /* ---- B4: right designation, wrong declared type.  The dependency's
     * contract constrains what may represent it. */
    {
        static const RmeField wrong_type[] = {
            { "temp",     "int",    "temperature" },
            { "pressure", "double", "pressure"    },
        };
        static const RmeArgType at = { "StepArgs", wrong_type, 2 };
        RmeTransitionBind t = { "step", &at, reads_base, 2 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(!r.ok && r.read == 0, "B4",
                  "field designating the dependency with the wrong type does not represent it");
    }

    /* ---- B5: reads declared with no argument interface at all. */
    {
        RmeTransitionBind t = { "step", nullptr, reads_base, 2 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(!r.ok, "B5", "declared reads with no ArgType are rejected");
    }

    /* ---- B6: empty Reads(T) is vacuously valid.  This is NOT a claim that
     * the body reads nothing — Bind(T) =/=> Body(T) reads only Reads(T). */
    {
        RmeTransitionBind t = { "step", &args_v1, nullptr, 0 };
        RmeBindResult r = rme_bind_valid(&t);
        rme_check(r.ok, "B6",
                  "empty Reads(T) is vacuously valid (no claim about the body)");
    }
}
