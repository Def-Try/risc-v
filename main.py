import sys
from math import ceil
from devices.cpu import CPU
from devices.memory import RAM

from utils import logger as logr

logger = logr.Logger(7)

def trace_exc(trace):
    traceback = ""
    if trace.tb_next:
        traceback += trace_exc(trace.tb_next) + "\n"
    traceback += f"File {trace.tb_frame.f_code.co_filename} line {trace.tb_lineno}"
    return traceback

def format_exception(e):
    klass, objekt, trace = e
    traceback = trace_exc(trace)
    formatted = f"{traceback}\n{klass.__name__}: {objekt}"
    return formatted

def parse_linker_map_file(file_content):
    symbols = []
    for line in file_content.splitlines():
        parts = line.split()
        if len(parts) == 3:
            address, _, symbol = parts
            symbols.append((int(address, 16), symbol))
    # Sorting the symbols by address
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

with open("linux/kernel.map", 'r') as file:
    file_content = file.read()
    symbols = parse_linker_map_file(file_content)

mem = RAM(logger)
with open("linux/kernel.img", 'rb') as file:
    linux_bytes = file.read()
with open("linux/device_tree_binary.dtb", 'rb') as file:
    devtree_bytes = file.read()
cpu = CPU(mem, logger)
cpu.integer_registers[11] = 0x80000000 + (len(linux_bytes)*2) - len(devtree_bytes) - 192
cpu.registers["pc"] = 0x80000000
mem.put_bytes(cpu.integer_registers[11], devtree_bytes)
mem.put_bytes(0x80000000, linux_bytes)
try:
    def callback():
        logger.log(3, "MAIN", f"Executing: {get_symbol_name(cpu.registers['pc'], symbols)}, at {cpu.registers['pc']:08x}")
    print(cpu.run(callback))
except BaseException as e:
    logger.log(1, "CRASH_HANDLER", "-="*40+"-")
    logger.log(1, "CRASH_HANDLER", "EXCEPTION OCCURED!")
    regs = [f"#{i:02d}: {reg:08x}, " for i,reg in enumerate(cpu.integer_registers)]
    for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
        logger.log(1, "CRASH_HANDLER", f"{a} {b} {c} {d}")
    logger.log(1, "CRASH_HANDLER", f"PC: {cpu.registers['pc']:08x}")
    logger.log(1, "CRASH_HANDLER", "")
    exc = sys.exc_info()
    tr = format_exception([exc[0], exc[1], exc[2]])
    for _ in tr.split("\n"):
        logger.log(1, "CRASH_HANDLER", _)
    logger.log(1, "CRASH_HANDLER", "-="*40+"-")
    logger.log(1, "CRASH_HANDLER", "Generating crash dump...")
    saveto = "./crash/"
    logger.log(1, "CRASH_HANDLER", f"Saving to {saveto}")
    def find_continuous_sequences(lst):
        sequences = []
        current_sequence = None
        for value in lst:
            if not current_sequence or value >= current_sequence[-1] + 2:
                current_sequence = [value]
                sequences.append(current_sequence)
            else:
                current_sequence.append(value)
        return sequences
    for region in find_continuous_sequences(sorted(list(mem.memory.keys()))):
        # print(min(region), max(region))
        # continue
        start = min(region)
        size = max(region) - start
        filename = f"{saveto}memory{start:08x}-{start+size:08x}.dmp"
        logger.log(1, "CRASH_HANDLER", f"  Writing memory dump: start={start:08x}, size={size:08x}, file={filename}")
        with open(filename, 'wb') as memdump:
            left = size
            while left > 0:
                logger.log(1, "CRASH_HANDLER", f"  Left to write: {left}...")
                memdump.write(mem.get_bytes(start, min(left, 1024*1024*16)))
                left -= 1024*1024*16
    logger.log(1, "CRASH_HANDLER", "  All written!")
    filename = f"{saveto}log.txt"
    logger.log(1, "CRASH_HANDLER", f"Writing logged data to {filename}")
    with open(filename, 'w', encoding='utf-8') as log:
        log.write(logger.textlog)