class Instruction:
    def __init__(self, instruct: int, args: list) -> None:
        self.instruct = instruct
        self.args = args

    def valid(self):
        return False

    def __call__(self):
        return False

class JAL(Instruction):
    instn = 0b1101111
    def __init__(self, fetched: bytes) -> None:
        rd = (fetched & 0b111110000000) >> 7
        val = (fetched & 0b10000000000000000000000000000000) >> 11 | \
              (fetched & 0b1111111111000000000000000000000) >> 20 | \
              (fetched & 0b100000000000000000000) >> 9 | \
              (fetched & 0b11111111000000000000)
        super().__init__(self.instn, [rd, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        cpu.integer_registers[self.args[0]] = cpu.registers["pc"] + 4
        cpu.registers["pc"] += self.args[1]

class EBREAK(Instruction):
    instn = 0b1110011
    def __init__(self, fetched: bytes) -> None:
        pass

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        pass

class FENCE(Instruction):
    instn = 0b0001111
    def __init__(self, fetched: bytes) -> None:
        pass

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        pass

class ANY_I(Instruction):
    instn = 0b0010011
    def __init__(self, fetched: bytes) -> None:
        func = fetched & 0b111000000000000
        func = func >> 12

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        pass

INSTRUCTIONS = [JAL, EBREAK, FENCE, ANY_I]
