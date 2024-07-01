class RAM:
    def __init__(self):
        self.memory = {}

    def put(self, to_addr: int, data: int):
        self.memory[to_addr] = data

    def get(self, from_addr: int) -> int:
        return self.memory.get(from_addr, 0)

    def get_bytes(self, from_addr: int, amount: int) -> bytes:
        return bytes([self.memory.get(addr, 0) for addr in range(from_addr, from_addr + amount)])

    def put_bytes(self, to_addr: int, data: bytes):
        for i, byte in enumerate(data):
            self.memory[to_addr + i] = byte

class RAM_ARRAYED:
    def __init__(self, size: int):
        self.size = size
        self.memory = bytearray(size)  # Use bytearray for efficient memory management

    def put(self, to_addr: int, data: int):
        if 0 <= to_addr < self.size:
            self.memory[to_addr] = data
        else:
            raise MemoryError(f"Invalid memory address: {to_addr}")

    def get(self, from_addr: int) -> int:
        if 0 <= from_addr < self.size:
            return self.memory[from_addr]
        else:
            raise MemoryError(f"Invalid memory address: {from_addr}")

    def get_bytes(self, from_addr: int, amount: int) -> bytes:
        if 0 <= from_addr < self.size and 0 <= from_addr + amount <= self.size:
            return bytes(self.memory[from_addr:from_addr + amount])
        else:
            raise MemoryError(f"Invalid memory access: from_addr={from_addr}, amount={amount}")

    def put_bytes(self, to_addr: int, data: bytes):
        if 0 <= to_addr < self.size and 0 <= to_addr + len(data) <= self.size:
            self.memory[to_addr:to_addr + len(data)] = data
        else:
            raise MemoryError(f"Invalid memory access: to_addr={to_addr}, data_length={len(data)}")
