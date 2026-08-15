/* NEGATIVE TEST — this file MUST FAIL to compile.
 *
 * The specification names this exact line as the anti-pattern F7/F8 exist
 * to forbid:
 *
 *     child->validated = parent->validated;
 *
 * It does not fail because a rule prohibits it.  It fails because no type
 * in the substrate has a `validated` member to write: validity is not a
 * field on a prototype, it is a handle produced by rme_validate().
 *
 * The same is attempted through the construction record, which likewise
 * carries authorization and provenance and no semantic predicate.
 */
#include "rme/validate.h"

void launder_proto(RmePrototype *child, const RmePrototype *parent);
void launder_constructed(RmeConstructed *child, const RmeConstructed *parent);

void launder_proto(RmePrototype *child, const RmePrototype *parent)
{
    child->validated = parent->validated;   /* no such member */
}

void launder_constructed(RmeConstructed *child, const RmeConstructed *parent)
{
    child->validated = parent->validated;   /* no such member */
}
