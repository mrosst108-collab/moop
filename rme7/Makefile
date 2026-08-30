CC      ?= cc
# C23 everywhere: newer compilers accept -std=c23, gcc 13 still calls it c2x.
CSTD    := $(shell $(CC) -std=c23 -E -x c /dev/null >/dev/null 2>&1 && echo c23 || echo c2x)
CFLAGS  ?= -std=$(CSTD) -Wall -Wextra -Wpedantic -g
BUILD   := build
LIB     := $(BUILD)/librme7.a
SRC     := $(wildcard *.c)
OBJ     := $(SRC:%.c=$(BUILD)/%.o)
HDR     := $(wildcard *.h)
TESTBIN := $(BUILD)/test_rme7

all: $(LIB)

$(LIB): $(OBJ)
	ar rcs $@ $^

$(BUILD)/%.o: %.c $(HDR) | $(BUILD)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD):
	mkdir -p $(BUILD)

$(TESTBIN): tests/test_rme7.c $(OBJ) | $(BUILD)
	$(CC) $(CFLAGS) -I. -o $@ $^

test: $(TESTBIN)
	$(TESTBIN)

clean:
	rm -rf $(BUILD)

.PHONY: all test clean
