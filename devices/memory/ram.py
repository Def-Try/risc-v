from numba.experimental import jitclass
from numba import types
from numba import jit
import numpy

class RAM_DICT:
    def __init__(self):
        self.memory = {}
        self.logger = logger

    def read(self, from_addr: int) -> bytes:
        raise NotImplementedError("TODO: implement!")

    def write(self, to_addr: int, data: bytearray):
        raise NotImplementedError("TODO: implement!")

@jitclass([('size', types.int32), ('memory', types.uint8[:])])
class RAM_BYTEARRAY_JIT:
    def __init__(self, size: int):
        self.size = size
        self.memory = numpy.zeros(size, dtype=numpy.uint8)

    def write(self, to_addr: int, data: list[int]):
        if to_addr + len(data) > self.size:
            raise MemoryError("Invalid memory address or size")
        for i in range(len(data)):
            self.memory[to_addr+i] = data[i]

    def read(self, from_addr: int, amount: int) -> list[int]:
        if amount == 1:
            if 0 <= from_addr < self.size:
                return [self.memory[from_addr]]
            else:
                raise MemoryError(f"Invalid memory address: {from_addr}")
        else:
            return [self.memory[from_addr+i] for i in range(amount)]


# Used as an adapter to AddressBus as numba does not know what bytearray is...
class RAM_BYTEARRAY:
    def __init__(self, size: int):
        self.ram = RAM_BYTEARRAY_JIT(size)

    def write(self, to_addr: int, data: bytearray):
        return self.ram.write(to_addr, list(data))

    def read(self, from_addr: int, amount: int):
        return bytearray(self.ram.read(from_addr, amount))