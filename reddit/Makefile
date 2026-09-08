CC      ?= cc
CSTD    := $(shell $(CC) -std=c23 -E -x c /dev/null >/dev/null 2>&1 && echo c23 || echo c2x)
CFLAGS  ?= -std=$(CSTD) -Wall -Wextra -Wpedantic -g
BUILD   := build
BIN     := $(BUILD)/reddit
TESTBIN := $(BUILD)/test_reddit

all: $(BIN)

$(BIN): src/main.c src/reddit.c src/rme7.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ src/main.c src/reddit.c -lm

$(TESTBIN): tests/test_reddit.c src/reddit.c src/rme7.h | $(BUILD)
	$(CC) $(CFLAGS) -Isrc -o $@ tests/test_reddit.c src/reddit.c -lm

$(BUILD):
	mkdir -p $(BUILD)

test: $(BIN) $(TESTBIN)
	sh tests/run_tests.sh

clean:
	rm -rf $(BUILD)

.PHONY: all test clean
