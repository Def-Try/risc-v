class RAM:
    def __init__(self, logger):
        self.memory = {}
        self.logger = logger

    def put(self, to_addr: int, size: int, data: int):
        self.logger.log(7, "RAM", f"writing {data:08x} w/ size {size} to {to_addr:08x}")
        self.put_bytes(to_addr, data.to_bytes(size))

    def get(self, from_addr: int, amount: int) -> int:
        self.logger.log(7, "RAM", f"reading from {from_addr:08x} w/ size {amount}")
        return int.from_bytes(self.get_bytes(from_addr, amount))

    def get_bytes(self, from_addr: int, amount: int) -> bytes:
        return bytes([self.memory.get(addr, 0) for addr in range(from_addr, from_addr + amount)])

    def put_bytes(self, to_addr: int, data: bytes):
        for i, byte in enumerate(data):
            self.memory[to_addr + i] = byte