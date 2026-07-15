# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

moop is a new programming language implemented in C23. Two influences anchor every design decision:

- **Naturalism** (Quorum, Andreas Stefik): syntax should read naturally and favor learnability; prefer design choices backed by evidence about how people read and write code.
- **Minimalism** (Io, Steve Dekorte): a tiny core with few concepts. Resist adding features, concepts, or implementation machinery — the whole language and its implementation should stay small enough to hold in your head.

When making language or implementation decisions, weigh them against both principles. If a change adds a concept, it needs to earn its place.

## Commands

```sh
make          # build the interpreter to build/moop
make test     # build, then run tests/run_tests.sh against build/moop
make clean    # remove build/
./build/moop            # start the REPL ("quit" exits)
./build/moop --version  # print version
```

There is no separate lint step; the build uses `-Wall -Wextra -Wpedantic` and warnings should be treated as errors to fix.

## Toolchain notes

- The Makefile probes the compiler and uses `-std=c23` when supported, falling back to `-std=c2x` (GCC 13, the compiler in this environment, only knows `c2x`). Both mean C23; write C23 code.
- Tests are plain POSIX sh (`tests/run_tests.sh`), driven by the `check` helper which compares expected vs. actual output of the built binary. Add new smoke tests as `check` lines there.

## Structure and state

- `src/` — interpreter sources. All `.c` files in `src/` are compiled and linked into the single `moop` binary; every `.c` file currently depends on `src/moop.h` (version constant lives there).
- `tests/run_tests.sh` — end-to-end smoke tests run against the built binary.

Current state: only the entry point exists (`src/main.c`: REPL loop, `--version`, file-argument stub). The lexer, parser, and evaluator are not implemented — the REPL deliberately reports "evaluation is not implemented yet" rather than pretending to work. Keep that honesty: never stub behavior in a way that silently looks functional.

Update this file as the interpreter grows (e.g., when the lexer/parser/evaluator land, document the pipeline and where each stage lives).
