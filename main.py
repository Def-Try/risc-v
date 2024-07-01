import sys
from math import ceil
from devices.cpu import CPU
from devices.memory import RAM

log_everything = False

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

mem = RAM()
with open("linux/kernel.img", 'rb') as file:
    linux_bytes = file.read()
with open("linux/device_tree_binary.dtb", 'rb') as file:
    code_bytes = file.read()
cpu = CPU(mem)
cpu.integer_registers[11] = 0x80000000 + (len(linux_bytes)*2) - len(code_bytes) - 192
cpu.registers["pc"] = 0x80000000
mem.put_bytes(cpu.integer_registers[11], code_bytes)
mem.put_bytes(0x80000000, linux_bytes)
try:
    def callback():
        print(f"Executing: {get_symbol_name(cpu.registers['pc'], symbols)}, at {cpu.registers['pc']:08x}")
    print(cpu.run(callback))
except BaseException as e:
    print("-="*40+"-")
    print("EXCEPTION OCCURED!")
    regs = [f"#{i:02d}: {reg:08x}, " for i,reg in enumerate(cpu.integer_registers)]
    for a,b,c,d in zip(regs[::4], regs[1::4], regs[2::4], regs[3::4]):
        print(f"{a} {b} {c} {d}")
    print(f"PC: {cpu.registers['pc']:08x}")
    print("")
    exc = sys.exc_info()
    tr = format_exception([exc[0], exc[1], exc[2]])
    print(tr)
    print("-="*40+"-")
