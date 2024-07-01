from utils.decoder import Decoder
import utils.conversions as converter

from config import log_everything

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
        drg, val = Decoder.decode_J_type(fetched)
        super().__init__(self.instn, [drg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        drg, val = self.args
        next_instruction = cpu.registers["pc"] + 4
        val = converter.interpret_as_21_bit_signed_value(val)
        cpu.registers["pc"] += val - 4
        cpu.integer_registers[drg] = next_instruction

        if log_everything: print(f"JAL -> {cpu.registers['pc']:08x}")

class JALR(Instruction):
    instn = 0b1100111
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        ist, drg, srg, val = self.args
        next_instruction = cpu.registers["pc"] + 4
        val = converter.interpret_as_12_bit_signed_value(val)
        cpu.registers["pc"] = cpu.integer_registers[srg] + val - 4
        cpu.integer_registers[drg] = next_instruction

        if log_everything: print(f"JALR -> {cpu.registers['pc']:08x}")

class EBREAK(Instruction):
    instn = 0b1110011
    def __init__(self, fetched: bytes) -> None:
        pass

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if log_everything: print("EBREAK")
        pass

class FENCE(Instruction):
    instn = 0b0001111
    def __init__(self, fetched: bytes) -> None:
        pass

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if log_everything: print("FENCE")
        pass

class ANY_INTGR_I(Instruction):
    instn = 0b0010011
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        ist, drg, srg, val = self.args
        if ist == 0: # ADDI
            if (val & 0x8000) != 0:
                val = -((~val & 0xFFF) + 1)
            if log_everything: print(f"ADDI -> x{drg} = x{srg} + {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] + val
            return

        if ist == 1: # SLLI
            if log_everything: print(f"SLLI -> x{drg} = x{srg} << {val & 0x1F}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] << (val & 0x1F)
            return

        if ist == 3: # SLTIU
            if log_everything: print(f"SLTIU -> x{drg} = x{srg} < {val}")
            cpu.integer_registers[drg] = \
                1 if cpu.integer_registers[srg] < val else 0
            return

        if ist == 4: # XORI
            val = converter.sign_extend_12_bit_value(val)
            if log_everything: print(f"XORI -> x{drg} = x{srg} ^ {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] ^ val
            return

        if ist == 5: # SRLI / SRAI
            if val >> 5 == 0x00:
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg] >> (val & 0x1F)
                if log_everything: print(f"SRLI -> x{drg} = x{srg} >> {val & 0x1F}")
                return
            if val >> 5 == 0x20:
                cpu.integer_registers[drg] = \
                    converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg]) >> (val & 0x1F)
                if log_everything: print(f"SRAI -> x{drg} = x{srg} >> {val & 0x1F}")
                return

        if ist == 6: # ORI
            val = sign_extend_12_bit_value(val)
            if log_everything: print(f"ORI -> x{drg} = x{srg} | {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] | val

        if ist == 7: # ANDI
            val = sign_extend_12_bit_value(val)
            if log_everything: print(f"ANDI -> x{drg} = x{srg} & {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] & val

        raise NotImplementedError(f"SUBInstruction not implemented: {ist:02x} / {ist:07b} / {ist}")

class ANY_INTGR(Instruction):
    instn = 0b0110011
    def __init__(self, fetched: bytes) -> None:
        ist1, ist2, srg1, srg2, drg = Decoder.decode_R_type(fetched)
        super().__init__(self.instn, [ist1, ist2, srg1, srg2, drg])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        ist1, ist2, srg1, srg2, drg = self.args
        if ist2 == 0x00:
            if ist1 == 0:
                if log_everything: print(f"ADD -> x{drg} = x{srg1} + x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] + cpu.integer_registers[srg2]
                return
            if ist1 == 1:
                if log_everything: print(f"SLL -> x{drg} = x{srg1} << x{srg2} & 0x1F")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] << (cpu.integer_registers[srg2] & 0x1F)
                return
            if ist1 == 2:
                if log_everything: print(f"SLT -> x{drg} = x{srg1} < x{srg2}")
                cpu.integer_registers[drg] = \
                    1 if converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        < converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2]) else 0
                return
            if ist1 == 3:
                if log_everything: print(f"SLTU -> x{drg} = x{srg1} < x{srg2}")
                cpu.integer_registers[drg] = \
                    1 if cpu.integer_registers[srg1] < cpu.integer_registers[srg2] else 0
                return
            if ist1 == 4:
                if log_everything: print(f"XOR -> x{drg} = x{srg1} ^ x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] ^ cpu.integer_registers[srg2]
                return
            if ist1 == 5:
                if log_everything: print(f"SRL -> x{drg} = x{srg1} >> x{srg2} & 0x1F")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] >> (cpu.integer_registers[srg2] & 0x1F)
                return
            if ist1 == 6:
                if log_everything: print(f"OR -> x{drg} = x{srg1} | x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] | cpu.integer_registers[srg2]
                return
            if ist1 == 7:
                if log_everything: print(f"AND -> x{drg} = x{srg1} & x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] & cpu.integer_registers[srg2]
                return
            raise NotImplementedError(f"SUBSUBInstruction of {ins2:02x} not implemented: {ist1:02x} / {ist1:07b} / {ist1}")
        if ist2 == 1:
            if ist1 == 0:
                if log_everything: print(f"MUL -> x{drg} = x{srg1} * x{srg2}")
                cpu.integer_registers[drg] = \
                    converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        * converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2])
                return
            if ist1 == 1:
                if log_everything: print(f"MULH -> x{drg} = x{srg1} * x{srg2}")
                cpu.integer_registers[drg] = \
                    (converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        * converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2])) >> 32
                return
            if ist1 == 3:
                if log_everything: print(f"MULHU -> x{drg} = x{srg1} * x{srg2}")
                cpu.integer_registers[drg] = \
                    (cpu.integer_registers[srg1] * cpu.integer_registers[srg2]) >> 32
                return
            if ist1 == 4:
                if log_everything: print(f"DIV -> x{drg} = x{srg1} / x{srg2}")
                #if converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2]) == 0:
                #    cpu.integer_registers[drg] = 0xFFFFFFFF
                #    return
                cpu.integer_registers[drg] = converter.convert_to_32_bit_unsigned_value(
                    converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        // converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2]))
                return
            raise NotImplementedError(f"SUBSUBInstruction of {ist2:02x} not implemented: {ist1:02x} / {ist1:07b} / {ist1}")
        raise NotImplementedError(f"SUBInstruction not implemented: {ist2:02x} / {ist2:07b} / {ist2}")

'''
            if self.args[1] == 0x01:
                if log_everything: print(f"MUL -> x{self.args[4]} = x{self.args[2]} * x{self.args[3]} & 0xFFFFFFFF")
                cpu.integer_registers[self.args[4]] = \
                    (cpu.integer_registers[self.args[2]] * cpu.integer_registers[self.args[3]]) & 0xFFFFFFFF
            if self.args[1] == 0x20:
                if log_everything: print(f"SUB -> x{self.args[4]} = x{self.args[2]} - x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] - cpu.integer_registers[self.args[3]]
        if self.args[0] == 1: # sll / mulh
            if self.args[1] == 0x00:
                
            if self.args[1] == 0x01:
                if log_everything: print(f"MULH -> x{self.args[4]} = x{self.args[2]} * x{self.args[3]} & 0xFFFFFFFF00000000")
                cpu.integer_registers[self.args[4]] = \
                    (cpu.integer_registers[self.args[2]] * cpu.integer_registers[self.args[3]]) & 0xFFFFFFFF00000000
        if self.args[0] == 2: # SLT / mulhsu
            if self.args[1] == 0x00:
                if log_everything: print(f"SLT -> x{self.args[4]} = x{self.args[2]} < x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    1 if cpu.integer_registers[self.args[2]] < cpu.integer_registers[self.args[3]] else 0
            if self.args[1] == 0x01:
                if log_everything: print(f"MULHSU -> x{self.args[4]} = x{self.args[2]} * x{self.args[3]} & 0xFFFFFFFF00000000")
                cpu.integer_registers[self.args[4]] = \
                    (cpu.integer_registers[self.args[2]] * cpu.integer_registers[self.args[3]]) & 0xFFFFFFFF00000000
        if self.args[0] == 3: # SLTU / mulu
            if self.args[1] == 0x00:
                if log_everything: print(f"SLTU -> x{self.args[4]} = x{self.args[2]} < x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    1 if cpu.integer_registers[self.args[2]] < cpu.integer_registers[self.args[3]] else 0
            if self.args[1] == 0x01:
                if log_everything: print(f"MULU -> x{self.args[4]} = x{self.args[2]} * x{self.args[3]} & 0xFFFFFFFF00000000")
                cpu.integer_registers[self.args[4]] = \
                    (cpu.integer_registers[self.args[2]] * cpu.integer_registers[self.args[3]]) & 0xFFFFFFFF00000000
        if self.args[0] == 4: # XOR / div
            if self.args[1] == 0x00:
                if log_everything: print(f"XOR -> x{self.args[4]} = x{self.args[2]} ^ x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] ^ cpu.integer_registers[self.args[3]]
            if self.args[1] == 0x01:
                if log_everything: print(f"DIV -> x{self.args[4]} = x{self.args[2]} / x{self.args[3]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] // cpu.integer_registers[self.args[3]]
        if self.args[0] == 5: # SRL / SRA / divu
            if self.args[1] == 0x00:
                if log_everything: print(f"SRL -> x{self.args[4]} = x{self.args[2]} >> x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] >> cpu.integer_registers[self.args[3]]
            if self.args[1] == 0x01:
                if log_everything: print(f"DIVU -> x{self.args[4]} = x{self.args[2]} / x{self.args[3]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] // cpu.integer_registers[self.args[3]]
            if self.args[1] == 0x20:
                if log_everything: print(f"SRA -> x{self.args[4]} = x{self.args[2]} >> x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] >> cpu.integer_registers[self.args[3]]
        if self.args[0] == 6: # OR / rem
            if self.args[1] == 0x00:
                if log_everything: print(f"OR -> x{self.args[4]} = x{self.args[2]} | x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] | cpu.integer_registers[self.args[3]]
            if self.args[1] == 0x01:
                if log_everything: print(f"REM -> x{self.args[4]} = x{self.args[2]} % x{self.args[3]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] % cpu.integer_registers[self.args[3]]
        if self.args[0] == 7: # AND / remu
            if self.args[1] == 0x00:
                if log_everything: print(f"AND -> x{self.args[4]} = x{self.args[2]} & x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] & cpu.integer_registers[self.args[3]]
            if self.args[1] == 0x01:
                if log_everything: print(f"REMU -> x{self.args[4]} = x{self.args[2]} % x{self.args[3]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] % cpu.integer_registers[self.args[3]]
'''

class AUIPC(Instruction):
    instn = 0b0010111
    def __init__(self, fetched: bytes) -> None:
        drg, val = Decoder.decode_U_type(fetched)
        super().__init__(self.instn, [drg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if self.args[1] & 0x00080000 != 0:
            self.args[1] = -((~self.args[1] & 0x000FFFFF) + 1)
        cpu.integer_registers[self.args[0]] = cpu.registers["pc"] + (self.args[1] << 12)
        if log_everything: print(f"AUIPC x{self.args[0]} = PC + {self.args[1] << 12}")

class LUI(Instruction):
    instn = 0b0110111
    def __init__(self, fetched: bytes) -> None:
        drg, val = Decoder.decode_U_type(fetched)
        super().__init__(self.instn, [drg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        cpu.integer_registers[self.args[0]] = self.args[1] << 12
        if log_everything: print(f"LUI x{self.args[0]} = {self.args[1] << 12}")

class BRANCH(Instruction):
    instn = 0b1100011
    def __init__(self, fetched: bytes) -> None:
        ist, srg1, srg2, val = Decoder.decode_B_type(fetched)
        super().__init__(self.instn, [ist, srg1, srg2, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if self.args[0] == 0: # beq
            if log_everything: print(f"BEQ x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] == cpu.integer_registers[self.args[2]]: return
            if log_everything: print("  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 1: # bne
            if log_everything: print(f"BNE x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] != cpu.integer_registers[self.args[2]]: return
            if log_everything: print("  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 4: # blt
            if log_everything: print(f"BLT x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] < cpu.integer_registers[self.args[2]]: return
            if log_everything: print("  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 5: # bge
            if log_everything: print(f"BGE x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] >= cpu.integer_registers[self.args[2]]: return
            if log_everything: print("  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 6: # bltu
            if log_everything: print(f"BLTU x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] <= cpu.integer_registers[self.args[2]]: return
            if log_everything: print("  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 7: # bgeu
            if log_everything: print(f"BGEU x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] >= cpu.integer_registers[self.args[2]]: return
            if log_everything: print("  JUMP")
            cpu.registers["pc"] += self.args[3]

class STORE(Instruction):
    instn = 0b0100011
    def __init__(self, fetched: bytes) -> None:
        ist, srg1, srg2, val = Decoder.decode_B_type(fetched)
        super().__init__(self.instn, [ist, srg1, srg2, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if self.args[0] == 0: # sb
            if log_everything: print(f"SB x{self.args[1]} + {self.args[3]}")
            memory.put(cpu.integer_registers[self.args[1]] + self.args[3],
                       cpu.integer_registers[self.args[2]] & 0xFF + \
                           memory.get(cpu.integer_registers[self.args[1]] + self.args[3]) & \
                               0xFFFFFF00)
        if self.args[0] == 1: # sh
            if log_everything: print(f"SH x{self.args[1]} + {self.args[3]}")
            memory.put(cpu.integer_registers[self.args[1]] + self.args[3],
                       cpu.integer_registers[self.args[2]] & 0xFFFF + \
                           memory.get(cpu.integer_registers[self.args[1]] + self.args[3]) & \
                               0xFFFF0000)
        if self.args[0] == 2: # sw
            if log_everything: print(f"SW x{self.args[1]} + {self.args[3]}")
            memory.put(cpu.integer_registers[self.args[1]] + self.args[3],
                       cpu.integer_registers[self.args[2]])

class LOAD(Instruction):
    instn = 0b0000011
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if self.args[0] == 0: # lb
            if log_everything: print(f"LB x{self.args[1]} = x{self.args[2]} + {self.args[3]}")
            cpu.integer_registers[self.args[1]] = memory.get(cpu.integer_registers[self.args[2]] + self.args[3]) & 0xFF
        if self.args[0] == 1: # lh
            if log_everything: print(f"LH x{self.args[1]} = x{self.args[2]} + {self.args[3]}")
            cpu.integer_registers[self.args[1]] = memory.get(cpu.integer_registers[self.args[2]] + self.args[3]) & 0xFFFF
        if self.args[0] == 2: # lw
            if log_everything: print(f"LW x{self.args[1]} = x{self.args[2]} + {self.args[3]}")
            cpu.integer_registers[self.args[1]] = memory.get(cpu.integer_registers[self.args[2]] + self.args[3]) & 0xFFFFFFFF
        if self.args[0] == 3: # lbu
            if log_everything: print(f"LBU x{self.args[1]} = x{self.args[2]} + {self.args[3]}")
            cpu.integer_registers[self.args[1]] = memory.get(cpu.integer_registers[self.args[2]] + self.args[3]) & 0xFF
        if self.args[0] == 4: # lhu
            if log_everything: print(f"LHU x{self.args[1]} = x{self.args[2]} + {self.args[3]}")
            cpu.integer_registers[self.args[1]] = memory.get(cpu.integer_registers[self.args[2]] + self.args[3]) & 0xFFFF

class ANY_ATOMIC(Instruction):
    instn = 0b0101111
    def __init__(self, fetched: bytes) -> None:
        ist, ist2, srg1, srg2, drg = Decoder.decode_R_type(fetched)
        super().__init__(self.instn, [ist, ist2, srg1, srg2, drg])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if self.args[0] != 0x02: raise ValueError("atomic invalid")
        if self.args[1] == 0x00:
            if log_everything: print(f"amoadd.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) + cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
        if self.args[1] == 0x01:
            if log_everything: print(f"amoswap.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]])
            cpu.integer_registers[self.args[4]], cpu.integer_registers[self.args[3]] = cpu.integer_registers[self.args[3]], cpu.integer_registers[self.args[4]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
        if self.args[1] == 0x02:
            if log_everything: print(f"lr.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]])
            cpu.reserved = cpu.integer_registers[self.args[2]]
        if self.args[1] == 0x03:
            if log_everything: print(f"sc.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            if cpu.reserved != cpu.integer_registers[self.args[2]]:
                cpu.integer_registers[self.args[4]] = 1
                return
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[3]])
            cpu.integer_registers[self.args[4]] = 0
        if self.args[1] == 0x04:
            if log_everything: print(f"amoxor.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) ^ cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
        if self.args[1] == 0x0A:
            if log_everything: print(f"amoor.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) | cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
        if self.args[1] == 0x0C:
            if log_everything: print(f"amoand.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) & cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
        if self.args[1] == 0x10:
            if log_everything: print(f"amomin.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = min(memory.get(cpu.integer_registers[self.args[2]]), cpu.integer_registers[self.args[3]])
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
        if self.args[1] == 0x14:
            if log_everything: print(f"amomax.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = max(memory.get(cpu.integer_registers[self.args[2]]), cpu.integer_registers[self.args[3]])
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])

INSTRUCTIONS = [
    JAL, JALR, BRANCH,
    EBREAK, FENCE,
    ANY_INTGR_I, ANY_INTGR, ANY_ATOMIC,
    AUIPC, LUI,
    STORE, LOAD
]
