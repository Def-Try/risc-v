import sys
import os
import zipfile
from math import ceil
from devices.cpu import CPU
from devices.memory import RAM_BYTEARRAY, RAM_DICT, AddressBus
from devices.uart import UART

from utils import logger as logr

import config_linux as config
#import config

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

ram = None
if config.RAM_TYPE == "BYTEARRAY":
    ram = RAM_BYTEARRAY(config.RAM_RANGE[1] - config.RAM_RANGE[0])
elif config.RAM_TYPE == "DICT":
    ram = RAM_DICT()
else:
    print(f"Unsupported ram type: {config.RAM_TYPE}. Should be one of ['DICT', 'BYTEARRAY']")
    exit(1)
uart = UART(logger)
bus = AddressBus([
    [config.UART_RANGE[0], config.UART_RANGE[1], uart],
    [config.RAM_RANGE[0], config.RAM_RANGE[1], ram]
])
cpu = CPU(bus, logger)

config.loader(logger, cpu, bus, uart)
instruction_no = 0
try:
    config.pre_cpu_start(logger)
    def callback():
        global instruction_no
        instruction_no += 1
        config.instruction_callback(logger, instruction_no)
    print(cpu.run(callback))
except BaseException as e:
    logger.enabled = True
    logger.log(1, "CRASH_HANDLER", "-="*40+"-")
    logger.log(1, "CRASH_HANDLER", "EXCEPTION OCCURED!")
    regs = cpu.get_registers_formatted()
    for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
        logger.log(1, "CRASH_HANDLER", f"{a} {b} {c} {d}")
    logger.log(1, "CRASH_HANDLER", f"PC: {cpu.registers['pc']:08x}")
    logger.log(1, "CRASH_HANDLER", f"I-No: {instruction_no}")
    logger.log(1, "CRASH_HANDLER", "")
    if hasattr(cpu, "profiling_data"):
        for inst,data in cpu.profiling_data.items():
            logger.log(1, "CRASH_HANDLER", f"PROFILING: {inst}: avg {sum(data) / len(data) * 1000:.4f}, min {min(data) * 1000:.4f}ms, max {max(data) * 1000:.4f}ms, ncalls {len(data)}")

    logger.log(1, "CRASH_HANDLER", f"I-No: {instruction_no}")
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
        if config.RAM_TYPE == "DICT":
            for region in find_continuous_sequences(sorted(list(ram.memory.keys()))):
                start = min(region)
                size = max(region) - start + 1
                filename = f"{saveto}memory{start:08x}-{start+size:08x}.dmp"
                logger.log(1, "CRASH_HANDLER", f"  Writing memory dump: start={start:08x}, size={size:08x}, file={filename}")
                with open(filename, 'wb') as memdump:
                    with dumpzip.open(filename, 'w') as memdumpzip:
                        left = size
                        got = 0
                        while left > 0:
                            logger.log(1, "CRASH_HANDLER", f"  Left to write: {left}...")
                            memdump.write(bus.read(config.RAM_RANGE[0]+start+got, min(left, 1024*1024)))
                            memdumpzip.write(bus.read(config.RAM_RANGE[0]+start+got, min(left, 1024*1024)))
                            left -= 1024*1024
                            got += 1024*1024
        elif config.RAM_TYPE == "BYTEARRAY":
            filename = f"{saveto}memory.dmp"
            logger.log(1, "CRASH_HANDLER", f"  Writing memory dump: file={filename}")
            with open(filename, 'wb') as memdump:
                with dumpzip.open(filename, 'w') as memdumpzip:
                    memdump.write(bus.read(config.RAM_RANGE[0], config.RAM_RANGE[1] - config.RAM_RANGE[0]))
                    memdumpzip.write(bus.read(config.RAM_RANGE[0], config.RAM_RANGE[1] - config.RAM_RANGE[0]))
        logger.log(1, "CRASH_HANDLER", "  All written!")
        filename = f"{saveto}log.txt"
        logger.log(1, "CRASH_HANDLER", f"Writing logged data to {filename}")
        with open(filename, 'w', encoding='utf-8') as log:
            with dumpzip.open(filename, 'w') as logzip:
                log.write(logger.textlog)
                logzip.write(logger.textlog.encode())

