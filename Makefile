CC      ?= cc
# C23 everywhere: newer compilers accept -std=c23, gcc 13 still calls it c2x.
CSTD    := $(shell $(CC) -std=c23 -E -x c /dev/null >/dev/null 2>&1 && echo c23 || echo c2x)
CFLAGS  ?= -std=$(CSTD) -Wall -Wextra -Wpedantic -g
BUILD   := build
BIN     := $(BUILD)/moop
SRC     := $(wildcard src/*.c)
OBJ     := $(SRC:src/%.c=$(BUILD)/%.o)
TESTBIN := $(BUILD)/test_core
# The number unit tests, twice: native 128-bit integers where the compiler
# has them, and the portable implementation, forced (MOOP_PORTABLE_WIDE).
NUMTEST := $(BUILD)/test_number $(BUILD)/test_number_portable

all: $(BIN)

$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^

HDR     := $(wildcard src/*.h)

$(BUILD)/%.o: src/%.c $(HDR) | $(BUILD)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD):
	mkdir -p $(BUILD)

$(TESTBIN): tests/test_core.c $(filter-out $(BUILD)/main.o,$(OBJ)) | $(BUILD)
	$(CC) $(CFLAGS) -Isrc -o $@ $^

$(BUILD)/test_number: tests/test_number.c src/number.c src/number.h | $(BUILD)
	$(CC) $(CFLAGS) -Isrc -o $@ tests/test_number.c src/number.c

$(BUILD)/test_number_portable: tests/test_number.c src/number.c src/number.h | $(BUILD)
	$(CC) $(CFLAGS) -DMOOP_PORTABLE_WIDE -Isrc -o $@ tests/test_number.c src/number.c

test: $(BIN) $(TESTBIN) $(NUMTEST)
	sh tests/run_tests.sh

clean:
	rm -rf $(BUILD)

.PHONY: all test clean
