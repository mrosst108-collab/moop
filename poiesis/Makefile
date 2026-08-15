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

.PHONY: all test clean std negative

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

clean:
	rm -rf $(BUILD)
