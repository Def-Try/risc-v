import sys
from math import ceil

from instructions import INSTRUCTIONS

log_everything = False

def trace_exc(trace):
    traceback = ""
    if trace.tb_next:
        traceback += trace_exc(trace.tb_next) + "\n"
    traceback += f"File {trace.tb_frame.f_code.co_filename} line {trace.tb_lineno}"
    return traceback

def format_exception(e):
    klass, objekt, trace = e
    traceback = trace_exc(trace)
    formatted = f"{traceback}\n{klass.__name__}: {objekt}"
    return formatted

class Memory:
    def __init__(self):
        self.memory = {}

    def put(self, to_addr: int, data: int):
        self.memory[to_addr] = data

    def get(self, from_addr: int) -> int:
        return self.memory.get(from_addr, 0)

    def get_bytes(self, from_addr: int, amount: int) -> bytes:
        return bytes([self.memory.get(addr, 0) for addr in range(from_addr, from_addr + amount)])

    def put_bytes(self, to_addr: int, data: bytes):
        for i, byte in enumerate(data):
            self.memory[to_addr + i] = byte

class CPU:
    __instructions = INSTRUCTIONS

    def __init__(self, memory: Memory):
        self.registers = {
            "pc": 0x80000000
        }
        self.integer_registers = [
             0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0,
        ]
        self.memory = memory

    def get_instruction(self, instn):
        for instruction in self.__instructions:
            if instruction.instn != instn: continue
            print(f"Instruction implemented: {instn:02x} / {instn:07b} / {instn} / {instruction.__name__}")
            return instruction
        raise NotImplementedError(f"Instruction not implemented: {instn:02x} / {instn:07b} / {instn}")

    def fetch_instruction(self):
        fetched = int.from_bytes(self.memory.get_bytes(self.registers["pc"], 2), 'little')
        self.registers["pc"] += 2

        inst_size = 16

        if fetched & 0b1111111 == 0b1111111:   # (80+16*nnn)-bit instruction
            self.registers["pc"] -= 2
            n = (fetched >> 12) & 0b111
            if n == 0b111:                     # >= 192 bit instruction
                raise NotImplementedError(f"Instruction size not implemented: {fetched:04x} / {fetched:16b}")
            x = (fetched >> 7) & 0b11111
            inst_size = bits = 80+16*n
            fetched = int.from_bytes(self.memory.get_bytes(self.registers["pc"], int(bits / 8)), 'little')
            self.registers["pc"] += int(bits / 8)
        elif fetched & 0b1111111 == 0b0111111: # 64 bit instruction
            self.registers["pc"] -= 2
            fetched = int.from_bytes(self.memory.get_bytes(self.registers["pc"], 8), 'little')
            inst_size = 64
            self.registers["pc"] += 8
        elif fetched & 0b111111 == 0b011111:   # 48 bit instruction
            self.registers["pc"] -= 2
            fetched = int.from_bytes(self.memory.get_bytes(self.registers["pc"], 6), 'little')
            inst_size = 48
            self.registers["pc"] += 6
        elif fetched & 0b11 == 0b11:           # 32 bit instruction
            self.registers["pc"] -= 2
            fetched = int.from_bytes(self.memory.get_bytes(self.registers["pc"], 4), 'little')
            inst_size = 32
            self.registers["pc"] += 4
        else:                                  # 16 bit instruction
            pass

        if log_everything: print(f"############## fetched: {fetched:08x}")
        if inst_size == 32:
            instruction = fetched & 0b01111111
        else:
            raise NotImplementedError(f"Instruction format not implemented: {fetched:016x} / inst_s {inst_size}")

        return self.get_instruction(instruction)(fetched)

    def run(self):
        graceful_exit = False
        while True:
            instruction = self.fetch_instruction()
            if not instruction.valid(): break
            instruction(self, self.memory)
            self.integer_registers[0] = 0
            for i in range(len(self.integer_registers)): self.integer_registers[i] = self.integer_registers[i] % (2**32-1)
        if not graceful_exit:
            return -1

with open("kernel.img", 'rb') as file:
    code_bytes = file.read()
program = b"\x01\x00\x80\x93"  # ADDI x5, x0, 5
program += b"\x01\x01\x80\x93"  # ADDI x6, x0, 10
program += b"\x02\x05\x00\x23"  # SW x5, 0(x6)
program += b"\x03\x06\x00\x23"  # LW x5, 0(x6)
program += b"\x00\x00\x00\x6f"  # JAL x0, label_print

#code_bytes = program

mem = Memory()
mem.put_bytes(0x80000000, code_bytes)
cpu = CPU(mem)

try:
    print(cpu.run())
except BaseException as e:
    print("-="*40+"-")
    print("EXCEPTION OCCURED!")
    regs = [f"#{i:02d}: {reg:08x}, " for i,reg in enumerate(cpu.integer_registers)]
    for a,b,c,d in zip(regs[::4], regs[1::3], regs[2::3], regs[3::3]):
        print(f"{a} {b} {c} {d}")
    print(f"PC: {cpu.registers['pc']:08x}")
    print("")
    exc = sys.exc_info()
    tr = format_exception([exc[0], exc[1], exc[2].tb_next])
    print(tr)
    print("-="*40+"-")
#    traceback.print_exc()
