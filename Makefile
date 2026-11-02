CC      ?= cc
# C23 everywhere: newer compilers accept -std=c23, gcc 13 still calls it c2x.
CSTD    := $(shell $(CC) -std=c23 -E -x c /dev/null >/dev/null 2>&1 && echo c23 || echo c2x)
CFLAGS  ?= -std=$(CSTD) -Wall -Wextra -Wpedantic -g
BUILD   := build
BIN     := $(BUILD)/moop
SRC     := $(wildcard src/*.c)
OBJ     := $(SRC:src/%.c=$(BUILD)/%.o)
TESTBIN := $(BUILD)/test_core

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

test: $(BIN) $(TESTBIN)
	sh tests/run_tests.sh

clean:
	rm -rf $(BUILD)

# --- moop-rv: the RV64 assembly implementation (docs/riscv.md) --------
# Separate targets: `make` and `make test` never need the RISC-V
# toolchain or QEMU.
#
# The declared target ISA: RV64I + M + Zbb + Zbs (a subset of the
# RVA22U64 profile), lp64 ABI. Every instruction in build/moop-rv must
# belong to it. Three guards hold it there: the assembler rejects other
# mnemonics (-march); `make test-rv` disassembles the final binary with
# only these extensions enabled and fails on anything undecodable
# (RV_MATTR — the same set in llvm-objdump's spelling); and the tests
# run on an emulated CPU whose ISA string must equal RV_MARCH (RV_CPU,
# QEMU 8.2 properties switching off everything else).
RV_MARCH   := rv64im_zbb_zbs
RV_MATTR   := +m,+zbb,+zbs
RV_ABI     := lp64
RV_CPU     := rv64,a=false,c=false,f=false,d=false,h=false,zca=false,zcd=false,zba=false,zbc=false,zicsr=false,zifencei=false,zicbom=false,zicboz=false,zihintntl=false,zihintpause=false,zawrs=false,zfa=false,zicntr=false,zihpm=false,sstc=false,svadu=false
RV_AS      ?= clang --target=riscv64-linux-gnu
RV_LD      ?= ld.lld
RV_OBJDUMP ?= llvm-objdump
RV_QEMU    ?= qemu-riscv64
RV_ASFLAGS := -march=$(RV_MARCH) -mabi=$(RV_ABI) -Isrc
RV_SRC     := $(wildcard rv/*.S)
RV_OBJ     := $(RV_SRC:rv/%.S=$(BUILD)/rv/%.o)
RV_BIN     := $(BUILD)/moop-rv
RV_PROBE   := $(BUILD)/rv/cpuinfo

rv: $(RV_BIN)

$(RV_BIN): $(RV_OBJ)
	$(RV_LD) -static -o $@ $^

$(BUILD)/rv/%.o: rv/%.S src/moop.h | $(BUILD)/rv
	$(RV_AS) $(RV_ASFLAGS) -c -o $@ $<

$(RV_PROBE): tests/rv_cpuinfo.S | $(BUILD)/rv
	$(RV_AS) $(RV_ASFLAGS) -c -o $@.o $<
	$(RV_LD) -static -o $@ $@.o

$(BUILD)/rv:
	mkdir -p $@

test-rv: $(BIN) $(RV_BIN) $(RV_PROBE)
	RV_RUN="$(RV_QEMU) -cpu $(RV_CPU)" RV_MARCH="$(RV_MARCH)" \
	RV_MATTR="$(RV_MATTR)" RV_OBJDUMP="$(RV_OBJDUMP)" \
	RV_PROBE="$(RV_PROBE)" sh tests/rv_tests.sh

.PHONY: all test clean rv test-rv
