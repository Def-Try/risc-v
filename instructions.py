from decoder import Decoder

log_everything = True

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
        next_instruction = cpu.registers["pc"] + 4
        if self.args[1] & 0x00100000 != 0:
            self.args[1] = -((~self.args[1] & 0x000FFFFF) + 1)
        cpu.registers["pc"] += self.args[1] - 4
        cpu.integer_registers[self.args[0]] = next_instruction

        if log_everything: print(f"JAL -> {cpu.registers['pc']}")

class JALR(Instruction):
    instn = 0b1100111
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        next_instruction = cpu.registers["pc"] + 4
        if self.args[3] & 0x00000800 != 0:
            self.args[3] = -((~self.args[3] & 0x00000FFF) + 1)
        cpu.registers["pc"] = cpu.integer_registers[self.args[2]] + self.args[3] - 4
        cpu.integer_registers[self.args[1]] = next_instruction

        if log_everything: print(f"JALR -> {cpu.registers['pc']}")

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
        if self.args[0] == 0: # addi
            if log_everything: print(f"ADDI -> x{self.args[1]} = x{self.args[2]} + {self.args[3]}")
            cpu.integer_registers[self.args[1]] = \
                cpu.integer_registers[self.args[2]] + self.args[3]
        if self.args[0] == 1: # slli
            if log_everything: print(f"SLLI -> x{self.args[1]} = x{self.args[2]} << {self.args[3] & 0x0f}")
            cpu.integer_registers[self.args[1]] = \
                cpu.integer_registers[self.args[2]] << (self.args[3] & 0x0F)
        if self.args[0] == 2: # slti
            if log_everything: print(f"SLTI -> x{self.args[1]} = x{self.args[2]} < {self.args[3]}")
            cpu.integer_registers[self.args[1]] = \
                1 if cpu.integer_registers[self.args[2]] < self.args[3] else 0
        if self.args[0] == 3: # sltiu
            if log_everything: print(f"SLTIU -> x{self.args[1]} = x{self.args[2]} < {self.args[3]}")
            cpu.integer_registers[self.args[1]] = \
                1 if cpu.integer_registers[self.args[2]] < self.args[3] else 0
        if self.args[0] == 4: # xori
            if log_everything: print(f"XORI -> x{self.args[1]} = x{self.args[2]} ^ {self.args[3]}")
            cpu.integer_registers[self.args[1]] = \
                cpu.integer_registers[self.args[2]] ^ self.args[3]
        if self.args[0] == 5: # srli
            if log_everything: print(f"SRLI -> x{self.args[1]} = x{self.args[2]} >> {self.args[3] & 0x0f}")
            cpu.integer_registers[self.args[1]] = \
                cpu.integer_registers[self.args[2]] >> (self.args[3] & 0x0F)
        if self.args[0] == 6: # ori
            if log_everything: print(f"ORI -> x{self.args[1]} = x{self.args[2]} | {self.args[3]}")
            cpu.integer_registers[self.args[1]] = \
                cpu.integer_registers[self.args[2]] | self.args[3]
        if self.args[0] == 7: # andi
            if log_everything: print(f"ANDI -> x{self.args[1]} = x{self.args[2]} & {self.args[3]}")
            cpu.integer_registers[self.args[1]] = \
                cpu.integer_registers[self.args[2]] & self.args[3]

class ANY_INTGR(Instruction):
    instn = 0b0110011
    def __init__(self, fetched: bytes) -> None:
        ist, ist2, srg1, srg2, drg = Decoder.decode_R_type(fetched)
        super().__init__(self.instn, [ist, ist2, srg1, srg2, drg])

    def valid(self):
        return True

    def __call__(self, cpu, memory):
        if self.args[0] == 0: # add / sub / mul
            if self.args[1] == 0x00:
                if log_everything: print(f"ADD -> x{self.args[4]} = x{self.args[2]} + x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] + cpu.integer_registers[self.args[3]]
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
                if log_everything: print(f"SLL -> x{self.args[4]} = x{self.args[2]} << x{self.args[2]}")
                cpu.integer_registers[self.args[4]] = \
                    cpu.integer_registers[self.args[2]] << cpu.integer_registers[self.args[3]]
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
