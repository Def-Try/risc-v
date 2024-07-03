class UART:
    def __init__(self, logger):
        self.logger = logger

    def read(self, from_addr: int) -> int:
        if from_addr == 5:
            return 0b01100000
        return 0

    def write(self, to_addr: int, data: int):
        if to_addr == 0:
        	print(chr(data), end='')