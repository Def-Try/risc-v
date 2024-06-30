from instructions import INSTRUCTIONS

class Memory:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def fetch_bytes(self,
                from_ptr: int = 0x00000000,
                amount  : int = 1) -> bytes:
        return self.data[from_ptr:from_ptr+amount]


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
        self.pc_offset = -0x80000000
        self.memory = memory

    def get_instruction(self, instn):
        for instruction in self.__instructions:
            if instruction.instn != instn: continue
            print(f"Instruction implemented: {instn:02x} / {instn:07b} / {instn}")
            return instruction
        raise NotImplementedError(f"Instruction not implemented: {instn:02x} / {instn:07b} / {instn}")

    def fetch_instruction(self):
        fetched = int.from_bytes(self.memory.fetch_bytes(self.registers["pc"] + self.pc_offset, 2), 'little')
        self.registers["pc"] += 2

        inst_size = 16

        if fetched & 0b1111111 == 0b1111111:   # (80+16*nnn)-bit instruction
            self.registers["pc"] -= 2
            n = (fetched >> 12) & 0b111
            if n == 0b111:                     # >= 192 bit instruction
                raise NotImplementedError(f"Instruction size not implemented: {fetched:04x} / {fetched:16b}")
            x = (fetched >> 7) & 0b11111
            inst_size = bits = 80+16*n
            fetched = int.from_bytes(self.memory.fetch_bytes(self.registers["pc"] + self.pc_offset, int(bits / 8)), 'little')
            self.registers["pc"] += int(bits / 8)
        elif fetched & 0b1111111 == 0b0111111: # 64 bit instruction
            self.registers["pc"] -= 2
            fetched = int.from_bytes(self.memory.fetch_bytes(self.registers["pc"] + self.pc_offset, 8), 'little')
            inst_size = 64
            self.registers["pc"] += 8
        elif fetched & 0b111111 == 0b011111:   # 48 bit instruction
            self.registers["pc"] -= 2
            fetched = int.from_bytes(self.memory.fetch_bytes(self.registers["pc"] + self.pc_offset, 6), 'little')
            inst_size = 48
            self.registers["pc"] += 6
        elif fetched & 0b11 == 0b11:           # 32 bit instruction
            self.registers["pc"] -= 2
            fetched = int.from_bytes(self.memory.fetch_bytes(self.registers["pc"] + self.pc_offset, 4), 'little')
            inst_size = 32
            self.registers["pc"] += 4
        else:                                  # 16 bit instruction
            pass

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
        if not graceful_exit:
            return -1

with open("kernel.img", 'rb') as file:
    code_bytes = file.read()
mem = Memory(code_bytes)
cpu = CPU(mem)

print(cpu.run())
