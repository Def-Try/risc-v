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