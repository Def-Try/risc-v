from .instructions import INSTRUCTIONS
from devices.memory import RAM

from config import log_everything

class CPU:
    __instructions = INSTRUCTIONS

    def __init__(self, memory: RAM):
        self.registers = {
            "pc": 0x00000000
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
            if log_everything: print(f"Instruction implemented: {instn:02x} / {instn:07b} / {instn} / {instruction.__name__}")
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

        if log_everything: print(f"############## fetched: {fetched:08x} at PC {self.registers['pc']:08x}")
        if inst_size == 32:
            instruction = fetched & 0b01111111
        else:
            raise NotImplementedError(f"Instruction format not implemented: {fetched:016x} / inst_s {inst_size}")

        return self.get_instruction(instruction)(fetched)

    def run(self, instruction_cb):
        graceful_exit = False
        while True:
            instruction = self.fetch_instruction()
            if not instruction.valid(): break
            instruction(self, self.memory)
            instruction_cb()
            self.integer_registers[0] = 0
            for i in range(len(self.integer_registers)): self.integer_registers[i] = self.integer_registers[i] & 0xFFFFFFFF
        if not graceful_exit:
            return -1
