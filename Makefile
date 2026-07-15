CC      ?= cc
# C23 everywhere: newer compilers accept -std=c23, gcc 13 still calls it c2x.
CSTD    := $(shell $(CC) -std=c23 -E -x c /dev/null >/dev/null 2>&1 && echo c23 || echo c2x)
CFLAGS  ?= -std=$(CSTD) -Wall -Wextra -Wpedantic -g
BUILD   := build
BIN     := $(BUILD)/moop
SRC     := $(wildcard src/*.c)
OBJ     := $(SRC:src/%.c=$(BUILD)/%.o)

all: $(BIN)

$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^

$(BUILD)/%.o: src/%.c src/moop.h | $(BUILD)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD):
	mkdir -p $(BUILD)

test: $(BIN)
	sh tests/run_tests.sh

clean:
	rm -rf $(BUILD)

.PHONY: all test clean
