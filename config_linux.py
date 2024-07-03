TRACEOUT_AT_PC = 0xFFFFFFFF
KILL_AT_PC = 0xFFFFFFFF
TRACEOUT_AT_INO = 114518
KILL_AT_INO = 114534

LOG_LEVEL = 7

RAM_RANGE = (0x80000000, 0xFFFFFFFF)

def parse_linker_map_file(file_content):
    symbols = []
    for line in file_content.splitlines():
        parts = line.split()
        if len(parts) == 3:
            address, _, symbol = parts
            symbols.append((int(address, 16), symbol))
    symbols.sort(key=lambda x: x[0])
    return symbols

def get_symbol_name(address, symbols):
    closest_symbol = 'Error parsing symbol'
    for symbol_address, symbol_name in symbols:
        if symbol_address <= address:
            closest_symbol = symbol_name
        else:
            break

    if closest_symbol == '_end':
        closest_symbol = 'Address outside of the kernel'
    else:
        closest_symbol += "()"
    return closest_symbol

cpu, bus, symbols = None, None, []
def loader(cpu_, bus_):
    global cpu, bus, symbols
    cpu, bus = cpu_, bus_
    with open("linux/kernel.map", 'r') as file:
        symbols = parse_linker_map_file(file.read())
    with open("linux/kernel.img", 'rb') as file:
        linux_bytes = file.read()
    with open("linux/device_tree_binary.dtb", 'rb') as file:
        devtree_bytes = file.read()
    cpu.integer_registers[11] = (0x80000000 + 64*1024*1024) - len(devtree_bytes) - 192
    cpu.registers["pc"] = 0x80000000
    bus.write(0x80000000, linux_bytes)
    bus.write(cpu.integer_registers[11], devtree_bytes)

def pre_cpu_start(logger):
    logger.enabled = LOG_LEVEL >= 9

_ps = ""
def instruction_callback(logger, instruction_no):
    global _ps
    if KILL_AT_INO < instruction_no or KILL_AT_PC < cpu.registers['pc']:
        raise SystemExit(0)
    symbol = get_symbol_name(cpu.registers['pc'], symbols)
    if LOG_LEVEL < 9:
        if _ps != symbol:
            logger.enabled = True
            logger.log(3, "MAIN", f"Executing at {cpu.registers['pc']:08x}, Instruction no is {instruction_no}, {symbol}")
            logger.enabled = False
            _ps = symbol
        if instruction_no % 250000 == 1:
            logger.enabled = False
        if cpu.registers['pc'] >= TRACEOUT_AT_PC or instruction_no >= TRACEOUT_AT_INO:
            logger.enabled = True
        if instruction_no % 250000 != 0 and not logger.enabled: return
    logger.enabled = True
    logger.log(3, "MAIN", f"Executing at {cpu.registers['pc']:08x}, Instruction no is {instruction_no}, {symbol}")
    regs = cpu.get_registers_formatted()
    for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
        logger.log(1, "MAIN", f"{a} {b} {c} {d}")
#    input("Press ENTER to step")
