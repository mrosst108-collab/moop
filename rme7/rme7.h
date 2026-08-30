#ifndef RME7_H
#define RME7_H

/* rme7 -- a C23 type layer for the RME-7 format.
 *
 * This library represents the format's DISTINCTIONS. It does not integrate
 * anything: there is no floating point here, and no manifold. What it can
 * do is refuse -- a slot in the wrong equation, a route with no contract, a
 * system declared at a rung it does not reach, a verdict asked to be a
 * score. See README.md for which refusals are checked and which are
 * prevented by the types themselves. */

#include "channel.h"
#include "profile.h"
#include "proto.h"
#include "slot.h"

#define RME7_VERSION "0.1.0"

#endif /* RME7_H */
