from decoder import Decoder

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
        rd, val = Decoder.decode_J_type(fetched)
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
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        pass

INSTRUCTIONS = [JAL, EBREAK, FENCE, ANY_I]
