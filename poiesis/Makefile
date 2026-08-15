# poiesis — RME-7 interoperability layer in ISO C23.
#
# Toolchain probe (spec: a toolchain fact, not part of the normative
# specification).  GCC 13 knows the language as -std=c2x; newer compilers
# accept -std=c23.  Both mean C23 — write C23 either way.
CC    ?= gcc
STD   := $(shell if $(CC) -std=c23 -E -x c /dev/null >/dev/null 2>&1; \
                 then echo c23; else echo c2x; fi)

# Compiler extensions are prohibited: -Wpedantic with a strict -std (not
# -std=gnu*) is what enforces that mechanically.
CFLAGS := -std=$(STD) -Wall -Wextra -Wpedantic -Werror -O2 -Isrc
BUILD  := build

SRC  := $(wildcard src/rme/*.c) $(wildcard src/awv/*.c)
OBJ  := $(patsubst %.c,$(BUILD)/%.o,$(SRC))
TSRC := $(wildcard tests/*.c)
TBIN := $(BUILD)/test_rme

NEG := $(wildcard tests/negative/*.c)

.PHONY: all test clean std negative layering protoc differential

all: $(TBIN)

std:
	@echo "CC=$(CC)  -std=$(STD)"

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(TBIN): $(OBJ) $(TSRC)
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(TSRC) $(OBJ) -o $@

test: $(TBIN)
	@./$(TBIN)

# Negative-compilation tests.  Each file encodes a way of manufacturing a
# validated prototype without crossing the validation boundary, and each
# MUST FAIL to compile.  A file that compiles is the failure signal: it
# means F7/F8 rest on convention rather than on the type system.
negative:
	@fail=0; \
	for f in $(NEG); do \
	  if $(CC) $(CFLAGS) -fsyntax-only $$f >/dev/null 2>&1; then \
	    echo "FAIL - $$f COMPILED; the invariant it attacks is unenforced"; \
	    fail=1; \
	  else \
	    echo "ok   - $$f rejected by the compiler"; \
	  fi; \
	done; \
	if [ $$fail -eq 0 ]; then \
	  echo ""; echo "all negative tests correctly refused"; \
	fi; \
	exit $$fail

# Dependency direction: AWV -> poiesis, NEVER the reverse.  src/rme/ must
# know nothing of AWV's vocabulary.  Checked mechanically, because a rule
# this easy to violate by a single convenient #include should not rest on
# anyone remembering it.
# Case-sensitive and word-bounded (grep -w).  A loose pattern produces false
# positives that train people to ignore the check -- an earlier version
# matched H_S inside rme_auth_subset, and a backslash-escaped version
# matched nothing at all while still reporting success.
AWV_TERMS := awv Sigma_U PageRank H_S delta

layering:
	@fail=0; \
	for t in $(AWV_TERMS); do \
	  if grep -rnwE "$$t" src/rme/ >/dev/null 2>&1; then \
	    echo "FAIL - src/rme/ mentions AWV term: $$t"; \
	    grep -rnwE "$$t" src/rme/ | head -3; \
	    fail=1; \
	  fi; \
	done; \
	for phrase in "Route 7C" "Fork [A-Z]"; do \
	  if grep -rnE "$$phrase" src/rme/ >/dev/null 2>&1; then \
	    echo "FAIL - src/rme/ mentions AWV phrase: $$phrase"; \
	    grep -rnE "$$phrase" src/rme/ | head -3; \
	    fail=1; \
	  fi; \
	done; \
	if grep -rn '#include *"awv/' src/rme/ >/dev/null 2>&1; then \
	  echo "FAIL - src/rme/ includes an AWV header"; fail=1; \
	fi; \
	if [ $$fail -eq 0 ]; then \
	  echo "ok   - src/rme/ is free of AWV vocabulary (AWV -> poiesis holds)"; \
	fi; \
	exit $$fail

# ProtoC builds and runs SEPARATELY.  It shares no headers, no objects and
# no test harness with src/rme/ -- the independence constraint is a build
# fact, not a promise.
PC_SRC := $(wildcard protoc/types/*.c) $(wildcard protoc/admissibility/*.c) \
          $(wildcard protoc/declaration/*.c) $(wildcard protoc/realization/*.c) \
          $(wildcard protoc/identity/*.c) $(wildcard protoc/composition/*.c) \
          $(wildcard protoc/graph/*.c)

protoc:
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -o $(BUILD)/pc_test protoc/tests/pc_test.c $(PC_SRC)
	@./$(BUILD)/pc_test

# The differential harness links BOTH substrates deliberately.  It is
# excluded from PC_SRC, so ProtoC proper still never sees an AWV header.
differential:
	@mkdir -p $(BUILD)
	$(CC) -std=$(STD) -Wall -Wextra -Wpedantic -O2 -Isrc \
	  -o $(BUILD)/pc_diff protoc/differential/pc_diff.c $(PC_SRC) $(wildcard src/rme/*.c)
	@./$(BUILD)/pc_diff

clean:
	rm -rf $(BUILD)
