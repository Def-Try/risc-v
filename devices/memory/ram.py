class RAM:
    def __init__(self, logger):
        self.memory = {}
        self.logger = logger

    def read(self, from_addr: int) -> bytes:
        return bytes([self.memory.get(from_addr, 0)])

    def write(self, to_addr: int, data: bytes):
        for i, byte in enumerate(data):
            self.memory[to_addr + i] = byte
