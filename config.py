TRACEOUT_AT_PC = 0xFFFFFFFF
TRACEOUT_AT_INO = 748620
LOG_LEVEL = 6

cpu, bus = None, None
def loader(cpu_, bus_):
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

def instruction_callback(logger, instruction_no):
    logger.log(7, "MAIN", f"Executing at {cpu.registers['pc']:08x}, Instruction no is {instruction_no}")