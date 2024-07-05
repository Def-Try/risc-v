class UART:
    def __init__(self, logger):
        self.logger = logger

    def read(self, from_addr: int, amount: int) -> int:
        if from_addr == 5:
            return bytearray([0b01100000])
        return bytearray([0])

    def write(self, to_addr: int, data: bytes):
        if to_addr != 0:
            return
        for byte in data:
        	print(chr(byte), end='')