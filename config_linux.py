TRACEOUT_AT_INO = 99999999
KILL_AT_INO = 99999999
TRACEOUT_PRINT_REGISTERS = False
DO_PRINT_CHANGED_SYMBOLS = False
REPORT_STATUS_EACH_INO = 2500

LOG_LEVEL = 7

RAM_TYPE   = "BYTEARRAY"
RAM_RANGE  = (0x80000000, 0x84000000)
UART_RANGE = (0x10000000, 0x10000008)

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
def loader(logger, cpu_, bus_, uart_):
    global cpu, bus, symbols
    cpu, bus = cpu_, bus_
    logger.log(3, "MAIN", "Loading map file...")
    with open("linux/kernel.map", 'r') as file:
        symbols = parse_linker_map_file(file.read())
    logger.log(3, "MAIN", "Loading kernel image...")
    with open("linux/kernel.img", 'rb') as file:
        linux_bytes = file.read()
    logger.log(3, "MAIN", "Loading device tree...")
    with open("linux/device_tree_binary.dtb", 'rb') as file:
        devtree_bytes = file.read()
    cpu.integer_registers[11] = (0x80000000 + 64*1024*1024) - len(devtree_bytes) - 192
    cpu.registers["pc"] = 0x80000000
    logger.log(3, "MAIN", "Writing kernel image to RAM...")
    bus.write(0x80000000, linux_bytes)
    logger.log(3, "MAIN", "Writing device tree to RAM...")
    bus.write(cpu.integer_registers[11], devtree_bytes)

def pre_cpu_start(logger):
    logger.enabled = LOG_LEVEL >= 9

_ps = ""
def instruction_callback(logger, instruction_no):
    global _ps
    if KILL_AT_INO < instruction_no:
        raise SystemExit(0)
    symbol = get_symbol_name(cpu.registers['pc'], symbols)
    if LOG_LEVEL < 9:
        if DO_PRINT_CHANGED_SYMBOLS:
            if _ps != symbol:
                logger.enabled = True
                logger.log(3, "MAIN", f"Executing at {cpu.registers['pc']:08x}, Instruction no is {instruction_no}, {symbol}")
                logger.enabled = False
                _ps = symbol
        if instruction_no % REPORT_STATUS_EACH_INO == 1:
            logger.enabled = False
        if instruction_no >= TRACEOUT_AT_INO:
            logger.enabled = True
        if instruction_no % REPORT_STATUS_EACH_INO != 0 and not logger.enabled: return
    logger.enabled = True
    logger.log(3, "MAIN", f"Executing at {cpu.registers['pc']:08x}, Instruction no is {instruction_no}, {symbol}")
    if TRACEOUT_PRINT_REGISTERS:
        regs = cpu.get_registers_formatted()
        for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
            logger.log(1, "MAIN", f"{a} {b} {c} {d}")
