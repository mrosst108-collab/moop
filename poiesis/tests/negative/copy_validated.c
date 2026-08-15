/* NEGATIVE TEST — this file MUST FAIL to compile.
 *
 * Obtaining a child's validity by copying the parent's validated object.
 * RmeValidated is incomplete outside validate.c, so it cannot be
 * dereferenced or assigned.
 *
 * Copying the POINTER is legal and harmless — it aliases the same validated
 * prototype.  What must be impossible is copying the validated STATE onto
 * a different subject, which is the laundering move F8c prohibits.
 */
#include "rme/validate.h"

void launder(RmeValidated *child, const RmeValidated *parent);

void launder(RmeValidated *child, const RmeValidated *parent)
{
    *child = *parent;   /* incomplete type: not assignable */
}
