#include "pc_declare.h"

void pc_declaration_init(PcDeclarationLog *log, PcDeclaration *store, size_t capacity)
{
    if (log == nullptr) return;
    log->entries = store;
    log->capacity = capacity;
    log->count = 0;
}

bool pc_declare(PcDeclarationLog *log, const PcSurface *a, const PcSurface *b,
                const PcConnectionSet *set)
{
    if (log == nullptr || log->entries == nullptr || set == nullptr
        || a == nullptr || b == nullptr) {
        return false;
    }
    if (set->count > 0 && set->edges == nullptr) {
        return false;   /* malformed, refused (S8) */
    }
    if (log->count >= log->capacity) {
        return false;   /* refused, not silently dropped */
    }
    log->entries[log->count++] = (PcDeclaration){ set, a, b };
    return true;
}

bool pc_is_declared(const PcDeclarationLog *log, const PcSurface *a,
                    const PcSurface *b, const PcConnectionSet *set)
{
    if (log == nullptr || log->entries == nullptr) return false;
    for (size_t i = 0; i < log->count; i++) {
        const PcDeclaration *d = &log->entries[i];
        if (d->set == set && d->a == a && d->b == b) {
            return true;
        }
    }
    return false;
}
