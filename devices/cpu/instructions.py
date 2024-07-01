from utils.decoder import Decoder
import utils.conversions as converter

class Instruction:
    def __init__(self, instruct: int, args: list) -> None:
        self.instruct = instruct
        self.args = args

    def valid(self):
        return False

    def __call__(self, cpu, memory, logger):
        return False

class JAL(Instruction):
    instn = 0b1101111
    def __init__(self, fetched: bytes) -> None:
        drg, val = Decoder.decode_J_type(fetched)
        super().__init__(self.instn, [drg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        drg, val = self.args
        next_instruction = cpu.registers["pc"] + 4
        val = converter.interpret_as_21_bit_signed_value(val)
        cpu.registers["pc"] += val - 4
        cpu.integer_registers[drg] = next_instruction

        logger.log(6, "CPU", f"JAL -> {cpu.registers['pc']:08x}")

class JALR(Instruction):
    instn = 0b1100111
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        ist, drg, srg, val = self.args
        next_instruction = cpu.registers["pc"] + 4
        val = converter.interpret_as_12_bit_signed_value(val)
        cpu.registers["pc"] = cpu.integer_registers[srg] + val - 4
        cpu.integer_registers[drg] = next_instruction

        logger.log(6, "CPU", f"JALR -> {cpu.registers['pc']:08x}")

class EBREAK_ECALL_CSR(Instruction):
    instn = 0b1110011
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        ist, drg, srg, val = self.args
        if ist == 0:
            #if val == 0:
            #    logger.log(6, "CPU", "ECALL")
            #    return
            #if val == 1:
            #    logger.log(6, "CPU", "EBREAK")
            #    return
            #if val == 0x105:
            #    logger.log(6, "CPU", "WFI")
            #    return
            #if val == 0x302:
            #    logger.log(6, "CPU", "MRET")
            #    return
            raise NotImplementedError(f"SUBSUBInstruction not implemented: {val:03x} / {val}")
        if ist == 1:
            logger.log(6, "CPU", f"CSR-RW x{srg} x{drg} {val:03x}")
            cur_val = cpu.csr_read(val)
            new_val = cpu.integer_registers[srg]
            cpu.csr_write(val, new_val)
            cpu.integer_registers[drg] = cur_val
            return
        if ist == 2:
            logger.log(6, "CPU", f"CSR-RS x{srg} x{drg} {val:03x}")
            cur_val = cpu.csr_read(val)
            new_val = cur_val | cpu.integer_registers[srg]
            cpu.csr_write(val, new_val)
            cpu.integer_registers[drg] = cur_val
            return
        if ist == 3:
            logger.log(6, "CPU", f"CSR-RC x{srg} x{drg} {val:03x}")
            cur_val = cpu.csr_read(val)
            new_val = cur_val & (~cpu.integer_registers[srg])
            cpu.csr_write(val, new_val)
            cpu.integer_registers[drg] = cur_val
            return
        if ist == 5:
            logger.log(6, "CPU", f"CSR-RWI {srg} x{drg} {val:03x}")
            cur_val = cpu.csr_read(val)
            new_val = srg
            cpu.csr_write(val, new_val)
            cpu.integer_registers[drg] = cur_val
            return
        raise NotImplementedError(f"SUBInstruction not implemented: {ist:02x} / {ist:07b} / {ist}")

class FENCE(Instruction):
    instn = 0b0001111
    def __init__(self, fetched: bytes) -> None:
        pass

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        logger.log(6, "CPU", "FENCE")

class ANY_INTGR_I(Instruction):
    instn = 0b0010011
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        ist, drg, srg, val = self.args
        if ist == 0: # ADDI
            if (val & 0x8000) != 0:
                val = -((~val & 0xFFF) + 1)
            logger.log(6, "CPU", f"ADDI -> x{drg} = x{srg} + {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] + val
            return

        if ist == 1: # SLLI
            logger.log(6, "CPU", f"SLLI -> x{drg} = x{srg} << {val & 0x1F}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] << (val & 0x1F)
            return

        if ist == 3: # SLTIU
            logger.log(6, "CPU", f"SLTIU -> x{drg} = x{srg} < {val}")
            cpu.integer_registers[drg] = \
                1 if cpu.integer_registers[srg] < val else 0
            return

        if ist == 4: # XORI
            val = converter.sign_extend_12_bit_value(val)
            logger.log(6, "CPU", f"XORI -> x{drg} = x{srg} ^ {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] ^ val
            return

        if ist == 5: # SRLI / SRAI
            if val >> 5 == 0x00:
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg] >> (val & 0x1F)
                logger.log(6, "CPU", f"SRLI -> x{drg} = x{srg} >> {val & 0x1F}")
                return
            if val >> 5 == 0x20:
                cpu.integer_registers[drg] = \
                    converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg]) >> (val & 0x1F)
                logger.log(6, "CPU", f"SRAI -> x{drg} = x{srg} >> {val & 0x1F}")
                return

        if ist == 6: # ORI
            val = sign_extend_12_bit_value(val)
            logger.log(6, "CPU", f"ORI -> x{drg} = x{srg} | {val}")
            cpu.integer_registers[drg] = \
                cpu.integer_registers[srg] | val

        if ist == 7: # ANDI
            val = sign_extend_12_bit_value(val)
            logger.log(6, "CPU", f"ANDI -> x{drg} = x{srg} & {val}")
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

    def __call__(self, cpu, memory, logger):
        ist1, ist2, srg1, srg2, drg = self.args
        if ist2 == 0x00:
            if ist1 == 0:
                logger.log(6, "CPU", f"ADD -> x{drg} = x{srg1} + x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] + cpu.integer_registers[srg2]
                return
            if ist1 == 1:
                logger.log(6, "CPU", f"SLL -> x{drg} = x{srg1} << x{srg2} & 0x1F")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] << (cpu.integer_registers[srg2] & 0x1F)
                return
            if ist1 == 2:
                logger.log(6, "CPU", f"SLT -> x{drg} = x{srg1} < x{srg2}")
                cpu.integer_registers[drg] = \
                    1 if converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        < converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2]) else 0
                return
            if ist1 == 3:
                logger.log(6, "CPU", f"SLTU -> x{drg} = x{srg1} < x{srg2}")
                cpu.integer_registers[drg] = \
                    1 if cpu.integer_registers[srg1] < cpu.integer_registers[srg2] else 0
                return
            if ist1 == 4:
                logger.log(6, "CPU", f"XOR -> x{drg} = x{srg1} ^ x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] ^ cpu.integer_registers[srg2]
                return
            if ist1 == 5:
                logger.log(6, "CPU", f"SRL -> x{drg} = x{srg1} >> x{srg2} & 0x1F")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] >> (cpu.integer_registers[srg2] & 0x1F)
                return
            if ist1 == 6:
                logger.log(6, "CPU", f"OR -> x{drg} = x{srg1} | x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] | cpu.integer_registers[srg2]
                return
            if ist1 == 7:
                logger.log(6, "CPU", f"AND -> x{drg} = x{srg1} & x{srg2}")
                cpu.integer_registers[drg] = \
                    cpu.integer_registers[srg1] & cpu.integer_registers[srg2]
                return
            raise NotImplementedError(f"SUBSUBInstruction of {ins2:02x} not implemented: {ist1:02x} / {ist1:07b} / {ist1}")
        if ist2 == 1:
            if ist1 == 0:
                logger.log(6, "CPU", f"MUL -> x{drg} = x{srg1} * x{srg2}")
                cpu.integer_registers[drg] = \
                    converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        * converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2])
                return
            if ist1 == 1:
                logger.log(6, "CPU", f"MULH -> x{drg} = x{srg1} * x{srg2}")
                cpu.integer_registers[drg] = \
                    (converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        * converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2])) >> 32
                return
            if ist1 == 3:
                logger.log(6, "CPU", f"MULHU -> x{drg} = x{srg1} * x{srg2}")
                cpu.integer_registers[drg] = \
                    (cpu.integer_registers[srg1] * cpu.integer_registers[srg2]) >> 32
                return
            if ist1 == 4:
                logger.log(6, "CPU", f"DIV -> x{drg} = x{srg1} / x{srg2}")
                #if converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2]) == 0:
                #    cpu.integer_registers[drg] = 0xFFFFFFFF
                #    return
                cpu.integer_registers[drg] = converter.convert_to_32_bit_unsigned_value(
                    converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg1]) \
                        // converter.interpret_as_32_bit_signed_value(cpu.integer_registers[srg2]))
                return
            raise NotImplementedError(f"SUBSUBInstruction of {ist2:02x} not implemented: {ist1:02x} / {ist1:07b} / {ist1}")
        raise NotImplementedError(f"SUBInstruction not implemented: {ist2:02x} / {ist2:07b} / {ist2}")

class AUIPC(Instruction):
    instn = 0b0010111
    def __init__(self, fetched: bytes) -> None:
        drg, val = Decoder.decode_U_type(fetched)
        super().__init__(self.instn, [drg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        drg, val = self.args
        val = converter.interpret_as_20_bit_signed_value(val)
        cpu.integer_registers[drg] = cpu.registers["pc"] + (val << 12)
        logger.log(6, "CPU", f"AUIPC x{drg} = PC + {val << 12}")

class LUI(Instruction):
    instn = 0b0110111
    def __init__(self, fetched: bytes) -> None:
        drg, val = Decoder.decode_U_type(fetched)
        super().__init__(self.instn, [drg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        drg, val = self.args
        cpu.integer_registers[drg] = val << 12
        logger.log(6, "CPU", f"LUI x{drg} = {val << 12}")

class BRANCH(Instruction):
    instn = 0b1100011
    def __init__(self, fetched: bytes) -> None:
        ist, srg1, srg2, val = Decoder.decode_B_type(fetched)
        super().__init__(self.instn, [ist, srg1, srg2, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        if self.args[0] == 0: # beq
            logger.log(6, "CPU", f"BEQ x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] == cpu.integer_registers[self.args[2]]: return
            logger.log(6, "CPU", "  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 1: # bne
            logger.log(6, "CPU", f"BNE x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] != cpu.integer_registers[self.args[2]]: return
            logger.log(6, "CPU", "  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 4: # blt
            logger.log(6, "CPU", f"BLT x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] < cpu.integer_registers[self.args[2]]: return
            logger.log(6, "CPU", "  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 5: # bge
            logger.log(6, "CPU", f"BGE x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] >= cpu.integer_registers[self.args[2]]: return
            logger.log(6, "CPU", "  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 6: # bltu
            logger.log(6, "CPU", f"BLTU x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] <= cpu.integer_registers[self.args[2]]: return
            logger.log(6, "CPU", "  JUMP")
            cpu.registers["pc"] += self.args[3]
        if self.args[0] == 7: # bgeu
            logger.log(6, "CPU", f"BGEU x{self.args[1]} x{self.args[2]} -> PC + {self.args[3]}")
            if not cpu.integer_registers[self.args[1]] >= cpu.integer_registers[self.args[2]]: return
            logger.log(6, "CPU", "  JUMP")
            cpu.registers["pc"] += self.args[3]

class STORE(Instruction):
    instn = 0b0100011
    def __init__(self, fetched: bytes) -> None:
        ist, srg1, srg2, val = Decoder.decode_B_type(fetched)
        super().__init__(self.instn, [ist, srg1, srg2, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        ist, srg1, srg2, val = self.args
        val = converter.interpret_as_12_bit_signed_value(val)
        addr = cpu.integer_registers[srg1] + val
        data = cpu.integer_registers[srg2]
        if ist == 0: # sb
            logger.log(6, "CPU", f"SB x{srg2} -> x{srg1} + {val}")
            memory.put(addr, 1, data & 0xFF)
        if ist == 1: # sh
            logger.log(6, "CPU", f"SH x{srg2} -> x{srg1} + {val}")
            memory.put(addr, 2, data & 0xFFFF)
        if ist == 2: # sw
            logger.log(6, "CPU", f"SW x{srg2} -> x{srg1} + {val}")
            memory.put(addr, 4, data & 0xFFFFFFFF)

class LOAD(Instruction):
    instn = 0b0000011
    def __init__(self, fetched: bytes) -> None:
        ist, drg, srg, val = Decoder.decode_I_type(fetched)
        super().__init__(self.instn, [ist, drg, srg, val])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        ist, drg, srg, val = self.args
        val = converter.interpret_as_12_bit_signed_value(val)
        addr = cpu.integer_registers[srg] + val
        if ist == 0: # lb
            logger.log(6, "CPU", f"LB x{drg} = x{srg} + {val}")
            value = memory.get(addr, 1)
            if value & 0b10000000 != 0:
                value = value | 0xFFFFFF00
            cpu.integer_registers[drg] = value
        if ist == 1: # lh
            logger.log(6, "CPU", f"LH x{drg} = x{srg} + {val}")
            value = memory.get(addr, 2)
            if value & 0x8000 != 0:
                value = value | 0xFFFF0000
            cpu.integer_registers[drg] = value
        if ist == 2: # lw
            logger.log(6, "CPU", f"LW x{drg} = x{srg} + {val}")
            value = memory.get(addr, 4)
            cpu.integer_registers[drg] = value
        if ist == 3: # lbu
            logger.log(6, "CPU", f"LBU x{drg} = x{srg} + {val}")
            value = memory.get(addr, 1)
            cpu.integer_registers[drg] = value
        if ist == 4: # lhu
            logger.log(6, "CPU", f"LHU x{drg} = x{srg} + {val}")
            value = memory.get(addr, 2)
            cpu.integer_registers[drg] = value

class ANY_ATOMIC(Instruction):
    instn = 0b0101111
    def __init__(self, fetched: bytes) -> None:
        ist, ist2, srg1, srg2, drg = Decoder.decode_R_type(fetched)
        super().__init__(self.instn, [ist, ist2, srg1, srg2, drg])

    def valid(self):
        return True

    def __call__(self, cpu, memory, logger):
        ist, ist2, srg1, srg2, drg = self.args
        if self.args[0] != 0x02: raise ValueError("atomic invalid")
        if self.args[1] == 0x00:
            logger.log(6, "CPU", f"amoadd.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) + cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return
        if self.args[1] == 0x01:
            logger.log(6, "CPU", f"amoswap.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]])
            cpu.integer_registers[self.args[4]], cpu.integer_registers[self.args[3]] = cpu.integer_registers[self.args[3]], cpu.integer_registers[self.args[4]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return
        if self.args[1] == 0x02:
            logger.log(6, "CPU", f"lr.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]])
            cpu.reserved = cpu.integer_registers[self.args[2]]
            return
        if self.args[1] == 0x03:
            logger.log(6, "CPU", f"sc.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            if cpu.reserved != cpu.integer_registers[self.args[2]]:
                cpu.integer_registers[self.args[4]] = 1
                return
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[3]])
            cpu.integer_registers[self.args[4]] = 0
            return
        if self.args[1] == 0x04:
            logger.log(6, "CPU", f"amoxor.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) ^ cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return
        if self.args[1] == 0x08:
            logger.log(6, "CPU", f"amoor.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) | cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return
        if self.args[1] == 0x0C:
            logger.log(6, "CPU", f"amoand.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = memory.get(cpu.integer_registers[self.args[2]]) & cpu.integer_registers[self.args[3]]
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return
        if self.args[1] == 0x10:
            logger.log(6, "CPU", f"amomin.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = min(memory.get(cpu.integer_registers[self.args[2]]), cpu.integer_registers[self.args[3]])
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return
        if self.args[1] == 0x14:
            logger.log(6, "CPU", f"amomax.w x{self.args[2]} x{self.args[3]} {self.args[4]}")
            cpu.integer_registers[self.args[4]] = max(memory.get(cpu.integer_registers[self.args[2]]), cpu.integer_registers[self.args[3]])
            memory.put(cpu.integer_registers[self.args[2]], cpu.integer_registers[self.args[4]])
            return

        raise NotImplementedError(f"SUBInstruction not implemented: {ist2:02x} / {ist2:07b} / {ist2}")

INSTRUCTIONS = [
    JAL, JALR, BRANCH,
    EBREAK_ECALL_CSR, FENCE,
    ANY_INTGR_I, ANY_INTGR, ANY_ATOMIC,
    AUIPC, LUI,
    STORE, LOAD
]
