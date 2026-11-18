#ifndef MOOP_NUMBER_H
#define MOOP_NUMBER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Numbers: bounded exact rationals (docs/foundations.md, F4, F5, F8, U1).
 *
 * A number is p/q in canonical form: q > 0, gcd(|p|, q) = 1, zero is
 * 0/1, and |p|, q <= 2^63 - 1. That is a finite set of rationals, not
 * all of them: whatever is representable is exact, and whatever is not
 * is refused, never wrapped, rounded or saturated.
 *
 * This is a user-layer value module: it computes on values in RAM and
 * never touches the tapes.
 *
 * Internally, reading a literal works on 128-bit magnitudes. Those are
 * the compiler's own 128-bit integers where it has them, and otherwise a
 * portable two-word implementation; compiling with MOOP_PORTABLE_WIDE
 * forces the portable one. Nothing of either appears in this interface. */

typedef struct {
    int64_t p;  /* numerator, carrying the sign */
    int64_t q;  /* denominator, always positive */
} MoopNumber;

#define MOOP_NUMBER_BOUND INT64_MAX  /* |p| and q are at most 2^63 - 1 */

/* Read a literal: an optional '-', digits, then optionally '/' and digits
 * (U1). Each written part is read exactly, up to 2^127 - 1; the sign
 * goes to the numerator; the fraction is reduced; the result must lie
 * within the bounds. Otherwise returns false with a reason in err. */
bool moop_number_read(const char *text, size_t len, MoopNumber *out,
                      char *err, size_t errlen);

/* The whole number n, which must satisfy |n| <= MOOP_NUMBER_BOUND. */
MoopNumber moop_number_whole(int64_t n);

bool moop_number_is_whole(MoopNumber n);

/* Exact equality. Canonical form makes it a comparison of parts. */
bool moop_number_equal(MoopNumber a, MoopNumber b);

/* The canonical text (F8): an integer when q is 1, otherwise p/q, with
 * the sign on p. It reads back as an equal number. Returns the length
 * written; a buffer of MOOP_NUMBER_TEXT_MAX bytes always suffices. */
#define MOOP_NUMBER_TEXT_MAX 48
size_t moop_number_text(MoopNumber n, char *buf, size_t cap);

/* Which 128-bit implementation this build uses: "native" or "portable". */
const char *moop_number_wide(void);

#endif
