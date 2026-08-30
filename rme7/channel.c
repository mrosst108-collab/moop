#include "channel.h"

#include <stddef.h>

bool rme7_channel_contracted(const Rme7Channel *ch) {
    if (ch == nullptr) return false;
    if (ch->translate == nullptr || ch->admit == nullptr ||
        ch->assimilate == nullptr) return false;
    if (ch->from == nullptr || ch->to == nullptr) return false;
    return ch->from != ch->to;   /* i != j */
}

Rme7Crossing rme7_channel_cross(const Rme7Channel *ch,
                                const void *claim, void *into) {
    if (!rme7_channel_contracted(ch))
        return (Rme7Crossing){ .reached = RME7_STAGE_TRANSLATE,
                               .verdict = RME7_REFUSED };

    if (!ch->translate(claim, into, ch->ctx))
        return (Rme7Crossing){ .reached = RME7_STAGE_TRANSLATE,
                               .verdict = RME7_REFUSED };

    if (ch->admit(into, ch->ctx) != RME7_ADMITTED)
        return (Rme7Crossing){ .reached = RME7_STAGE_ADMIT,
                               .verdict = RME7_REFUSED };

    if (!ch->assimilate(into, ch->ctx))
        return (Rme7Crossing){ .reached = RME7_STAGE_ASSIMILATE,
                               .verdict = RME7_REFUSED };

    return (Rme7Crossing){ .reached = RME7_STAGE_COMPLETE,
                           .verdict = RME7_ADMITTED };
}

const char *rme7_stage_name(Rme7Stage stage) {
    switch (stage) {
    case RME7_STAGE_TRANSLATE:  return "translate";
    case RME7_STAGE_ADMIT:      return "admit";
    case RME7_STAGE_ASSIMILATE: return "assimilate";
    case RME7_STAGE_COMPLETE:   return "complete";
    }
    return "unknown";
}

bool rme7_composed(const Rme7Channel *channels, size_t count) {
    for (size_t i = 0; i < count; i++)
        if (rme7_channel_contracted(&channels[i])) return true;
    return false;
}
