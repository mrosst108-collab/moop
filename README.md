# moop

moop is a new programming language. Its implementation is written in C23.

Two influences guide its design:

- **Naturalism**, in the spirit of Quorum (Andreas Stefik): syntax that reads
  naturally and favors learnability, with design choices grounded in evidence
  about how people actually read and write code.
- **Minimalism**, in the spirit of Io (Steve Dekorte): a tiny core with few
  concepts, kept simple enough to hold in your head — implementation included.

## Building

```sh
make        # builds build/moop
make test   # runs the smoke tests
make clean
```

Requires a C compiler with C23 support (`-std=c23`, or `-std=c2x` on older
compilers such as GCC 13 — the Makefile detects which one to use).

## Status

Early days: the project currently builds a REPL shell and version banner.
The lexer, parser, and evaluator do not exist yet.
