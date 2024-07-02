from .instructions import INSTRUCTIONS
from devices.memory import AddressBus

from utils.logger import Logger

MACHINE_MODE    = 0b11
SUPERVISOR_MODE = 0b01
USER_MODE       = 0b00

mask_mstatus_MIE  = 0x0008
mask_mstatus_MPIE = 0x0080
mask_mstatus_MPP  = 0x1800

class CPU:
    __instructions = INSTRUCTIONS

    def __init__(self, memory: AddressBus, logger: Logger):
        self.logger = logger
        self.registers = {
            "pc": 0x00000000
        }
        self.register_ids = { # CSR-to-regname dict
            0x139: "hvc0", # Xen hypervisor console out
            0x140: "sscratch", # Scratch register for supervisor trap handlers
            0x300: "mstatus", # Machine Status register
            0x304: "mie", # Machine Interrupt Enable
            0x305: "mtvec", # Machine trap-handler base address
            0x340: "mscratch", # Scratch register
            0x341: "mepc", # Machine exception PC / Instruction pointer
            0x342: "mcause", # Machine trap cause
            0x343: "mtval", # Machine bad address or instruction
            0x344: "mip", # Machine Interrupt Pending
            0x3a0: "pmpcfg0", # Physical memory protection configuration
            0x3b0: "pmpaddr0", # Physical memory protection address register
            0xf11: "mvendorid", # Machine Vendor ID
            0xf12: "marchid", # Machine Architecture ID
            0xf13: "mimpid", # Machine Implementation ID
            0xf14: "mhartid", # Hardware thread ID
        }
        self.hardwires = { # CSR register hardwires
            "sscratch": 0xffffffff,
            "mvendorid": 0xff0ff0ff,
            "mhartid": 0,
            "pmpcfg0": 0,
            "pmpaddr0": 0,
            "mvendorid": 0,
            "marchid": 0,
            "mimpid": 0,
            "hvc0": 0
        }
        self.integer_registers = [
             0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0,
        ]
        self.memory = memory
        self.previous_privilege_mode = USER_MODE
        self.privilege_mode = MACHINE_MODE
        self.previous_interrupts_enable = False
        self.interrupts_enable = False

    def get_registers_formatted(self):
        regs = [f"#{i:02d}: {reg:08x}, " for i,reg in enumerate(self.integer_registers)] + [f"{n:8}: {reg:08x}, " for n,reg in self.registers.items() if n != "pc"] + [f"mstatus : {self.csr_read(0x300):08x}"]
        regs = regs + [" "] * 4
        return regs

    def csr_read(self, address):
        regname = self.register_ids.get(address, "NONE")
        if regname == "NONE": return 0
        if self.hardwires.get(regname): return self.hardwires[regname]
        if regname == "mstatus":
            mstatus_value = 0
            if self.interrupts_enable:
                mstatus_value |= mask_mstatus_MIE
            if self.previous_interrupts_enable == True:
                mstatus_value |= mask_mstatus_MPIE
            mstatus_value |= (self.previous_privilege_mode << 11)
            return mstatus_value
        else:
            return self.registers.get(regname, 0)

    def csr_write(self, address, data):
        regname = self.register_ids.get(address, "NONE")
        if regname == "NONE": return
        if regname == "hvc0": print(chr(data), end='', flush=True)
        if self.hardwires.get(regname): return
        if regname == "mstatus":
            changed_bits = self.csr_read(address) ^ data
            if changed_bits: return
            if changed_bits & mask_mstatus_MIE == mask_mstatus_MIE:
                if data & mask_mstatus_MIE:
                    self.interrupts_enable = True
                    return
                self.interrupts_enable = False
            if changed_bits & mask_mstatus_MPIE == mask_mstatus_MPIE:
                if data & mask_mstatus_MPIE:
                    self.previous_interrupts_enable = True
                    return
                self.previous_interrupts_enable = False
            if changed_bits & mask_mstatus_MPP == mask_mstatus_MPP:
                self.previous_privilege_mode = ((data & mask_mstatus_MPP) >> 11) & 0b11
        else:
            self.registers[regname] = data

    def int_read(self, n):
        return self.integer_registers[n]

    def int_write(self, n, v):
#        if n in [10, 12]:
#            o = self.logger.enabled; self.logger.enabled = True
#            self.logger.log(4, "CPU", f"Register write: x{n}: {self.int_read(n):08x} -> {v:08x}")
#            self.logger.enabled = o
        self.integer_registers[n] = v % 0xFFFFFFFF

    def get_instruction(self, instn):
        for instruction in self.__instructions:
            if instruction.instn != instn: continue
            self.logger.log(8, "CPU", f"Instruction implemented: {instn:02x} / {instn:07b} / {instn} / {instruction.__name__}")
            return instruction
        raise NotImplementedError(f"Instruction not implemented: {instn:02x} / {instn:07b} / {instn}")

    def fetch_instruction(self):
        fetched = int.from_bytes(self.memory.read(self.registers["pc"], 2), 'little')
        inst_size = 16

        if fetched & 0b1111111 == 0b1111111:   # (80+16*nnn)-bit instruction
            n = (fetched >> 12) & 0b111
            if n == 0b111:                     # >= 192 bit instruction
                raise NotImplementedError(f"Instruction size not implemented: {fetched:04x} / {fetched:16b}")
            x = (fetched >> 7) & 0b11111
            inst_size = bits = 80+16*n
            fetched = int.from_bytes(self.memory.read(self.registers["pc"], bits // 8), 'little')
        elif fetched & 0b1111111 == 0b0111111: # 64 bit instruction
            fetched = int.from_bytes(self.memory.read(self.registers["pc"], 8), 'little')
            inst_size = 64
        elif fetched & 0b111111 == 0b011111:   # 48 bit instruction
            fetched = int.from_bytes(self.memory.read(self.registers["pc"], 6), 'little')
            inst_size = 48
        elif fetched & 0b11 == 0b11:           # 32 bit instruction
            fetched = int.from_bytes(self.memory.read(self.registers["pc"], 4), 'little')
            inst_size = 32
        else:                                  # 16 bit instruction
            pass

        self.logger.log(8, "CPU", f"############## fetched: {fetched:08x} at PC {self.registers['pc']:08x}")
        if inst_size == 32:
            instruction = fetched & 0b01111111
        else:
            raise NotImplementedError(f"Instruction format not implemented: {fetched:016x} / inst_s {inst_size}")

        inst = self.get_instruction(instruction)(fetched)
        inst.inst_size = inst_size
        return inst

    def run(self, instruction_cb):
        graceful_exit = False
        while True:
            instruction = self.fetch_instruction()
            if not instruction.valid(): break
            try:
                instruction_cb()
                jumped_pc = instruction(self, self.memory, self.logger)
                self.integer_registers[0] = 0
                for i in range(len(self.integer_registers)):
                    self.integer_registers[i] = self.integer_registers[i] & 0xFFFFFFFF
                if not jumped_pc:
                    self.registers["pc"] += instruction.inst_size // 8
            except:
                self.integer_registers[0] = 0
                for i in range(len(self.integer_registers)):
                    self.integer_registers[i] = self.integer_registers[i] & 0xFFFFFFFF
                raise
        if not graceful_exit:
            return -1
