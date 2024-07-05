TRACEOUT_AT_PC = 0xFFFFFFFF
TRACEOUT_AT_INO = 748620

LOG_LEVEL = 6

RAM_RANGE  = (0x80000000, 0xFFFFFFFF)
UART_RANGE = (0x10000000, 0x10000008)

cpu, bus = None, None
def loader(logger, cpu_, bus_, uart_):
    global cpu, bus
    cpu, bus = cpu_, bus_
    with open("program/code.img", 'rb') as file:
        code_bytes = file.read()
    def reverseGroup(inp,k):
        start = 0
        result = []
        while (start<len(inp)):
            if len(inp[start:])<k:
                result = result + list(reversed(inp[start:]))
                break
            result = result + list(reversed(inp[start:start + k]))
            start = start + k
        return result
    code_bytes = bytes(reverseGroup(list(code_bytes), 4))
    cpu.registers["pc"] = 0x80000000
    bus.write(0x80000000, code_bytes)

def pre_cpu_start(logger):
    logger.enabled = True

# prevregs = []
def instruction_callback(logger, instruction_no):
    # global prevregs
    logger.log(7, "MAIN", f"Executing at {cpu.registers['pc']:08x}, Instruction no is {instruction_no}")
    # regs = [x for x in cpu.get_registers_formatted() if x not in prevregs] + [""] * 4
    regs = cpu.get_registers_formatted()
    for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
        logger.log(1, "MAIN", f"{a} {b} {c} {d}")
