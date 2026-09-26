/* NEGATIVE TEST — this file MUST FAIL to compile.
 *
 * Forging a validated prototype without crossing rme_validate().
 * RmeValidated is an opaque incomplete type, so an object of it cannot be
 * declared or initialized outside validate.c.
 *
 * If this compiles, the validation boundary is a convention rather than a
 * type-level barrier, and F7/F8 are unenforced.
 */
#include "rme/validate.h"

const RmeValidated *forge(const RmePrototype *p);

const RmeValidated *forge(const RmePrototype *p)
{
    static RmeValidated forged = { p };   /* incomplete type: not declarable */
    return &forged;
}
