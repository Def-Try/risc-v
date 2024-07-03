class RAM_DICT:
    def __init__(self, logger):
        self.memory = {}
        self.logger = logger

    def read(self, from_addr: int) -> bytes:
        return self.memory.get(from_addr, 0)

    def write(self, to_addr: int, data: int):
        self.memory[to_addr + i] = data

class RAM_BYTEARRAY:
    def __init__(self, logger, size: int):
        self.size = size
        self.memory = bytearray(size)

    def write(self, to_addr: int, data: int):
        if to_addr + len(data) > self.size:
            raise MemoryError("Invalid memory address or size")
        self.memory[to_addr:to_addr+len(data)] = data

    def read(self, from_addr: int, amount: int) -> bytes:
        if amount == 1:
            if 0 <= from_addr < self.size:
                return self.memory[from_addr]
            else:
                raise MemoryError(f"Invalid memory address: {from_addr}")
        else:
            return self.memory[from_addr:from_addr+amount]