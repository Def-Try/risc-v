import sys
import os
import zipfile
from math import ceil
from devices.cpu import CPU
from devices.memory import RAM, AddressBus

from utils import logger as logr

import config

logger = logr.Logger(config.LOG_LEVEL)

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

ram = RAM(logger)
bus = AddressBus([[0x80000000, 0xFFFFFFFF, ram]])
cpu = CPU(bus, logger)

with open("linux/kernel.map", 'r') as file:
    file_content = file.read()
    symbols = parse_linker_map_file(file_content)
with open("linux/kernel.img", 'rb') as file:
    linux_bytes = file.read()
with open("linux/device_tree_binary.dtb", 'rb') as file:
    devtree_bytes = file.read()
cpu.integer_registers[11] = (0x80000000 + 64*1024*1024) - len(devtree_bytes) - 192
cpu.registers["pc"] = 0x80000000
ram.write(0x80000000, linux_bytes)
ram.write(cpu.integer_registers[11], devtree_bytes)
i = 0
try:
    ps = ""
    def callback():
        global i,ps
        i += 1
        symbol = get_symbol_name(cpu.registers['pc'], symbols)
        if config.LOG_LEVEL < 9:
            if ps != symbol:
                logger.enabled = True
                logger.log(3, "MAIN", f"Executing: {symbol}, at {cpu.registers['pc']:08x}, Instruction no is {i}")
                logger.enabled = False
                ps = symbol
            if i % 250000 == 1:
                logger.enabled = False
            if cpu.registers['pc'] >= config.TRACEOUT_AT_PC or i >= config.TRACEOUT_AT_INO:
                logger.enabled = True
            if i % 250000 != 0 and not logger.enabled: return
        logger.enabled = True
        logger.log(3, "MAIN", f"Executing: {symbol}, at {cpu.registers['pc']:08x}, Instruction no is {i}")
    logger.enabled = config.LOG_LEVEL >= 9
    print(cpu.run(callback))
except BaseException as e:
    logger.enabled = True
    logger.log(1, "CRASH_HANDLER", "-="*40+"-")
    logger.log(1, "CRASH_HANDLER", "EXCEPTION OCCURED!")
    regs = [f"#{i:02d}: {reg:08x}, " for i,reg in enumerate(cpu.integer_registers)] + [f"{n:8}: {reg:08x}, " for n,reg in cpu.registers.items()] + [f"mstatus : {cpu.csr_read(0x300):08x}"]
    regs = regs + [" "] * 4
    for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
        logger.log(1, "CRASH_HANDLER", f"{a} {b} {c} {d}")
    logger.log(1, "CRASH_HANDLER", f"PC: {cpu.registers['pc']:08x}")
    logger.log(1, "CRASH_HANDLER", f"I-No: {i}")
    logger.log(1, "CRASH_HANDLER", f"Symbol: {get_symbol_name(cpu.registers['pc'], symbols)}")
    logger.log(1, "CRASH_HANDLER", "")
    exc = sys.exc_info()
    tr = format_exception([exc[0], exc[1], exc[2]])
    for _ in tr.split("\n"):
        logger.log(1, "CRASH_HANDLER", _)
    logger.log(1, "CRASH_HANDLER", "-="*40+"-")
    logger.log(1, "CRASH_HANDLER", "Generating crash dump...")
    saveto = "crash/"
    if not os.path.exists(saveto):
        os.makedirs(saveto)
    for filename in os.listdir(saveto):
        file_path = os.path.join(saveto, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
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

    with zipfile.ZipFile(f'{saveto}crashdump.zip', 'w') as dumpzip:
        for region in find_continuous_sequences(sorted(list(ram.memory.keys()))):
            start = min(region)
            size = max(region) - start
            filename = f"{saveto}memory{start:08x}-{start+size:08x}.dmp"
            logger.log(1, "CRASH_HANDLER", f"  Writing memory dump: start={start:08x}, size={size:08x}, file={filename}")
            with open(filename, 'wb') as memdump:
                with dumpzip.open(filename, 'w') as memdumpzip:
                    left = size
                    got = 0
                    while left > 0:
                        logger.log(1, "CRASH_HANDLER", f"  Left to write: {left}...")
                        memdump.write(bus.read(start+got, min(left, 1024*1024)))
                        memdumpzip.write(bus.read(start+got, min(left, 1024*1024)))
                        left -= 1024*1024
                        got += 1024*1024
        logger.log(1, "CRASH_HANDLER", "  All written!")
        filename = f"{saveto}log.txt"
        logger.log(1, "CRASH_HANDLER", f"Writing logged data to {filename}")
        with open(filename, 'w', encoding='utf-8') as log:
            with dumpzip.open(filename, 'w') as logzip:
                log.write(logger.textlog)
                logzip.write(logger.textlog.encode())

