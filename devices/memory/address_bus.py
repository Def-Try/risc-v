class AddressBus:
    def __init__(self, devices: list):
        self.devices = devices

    def read_single(self, address: int) -> int:
        for start, end, device in self.devices:
            if address < start or address > end: continue
            return device.read(address - start, 1) & 0xFF
        raise ValueError(f"Address {address:08x} out of bounds")
    def write_single(self, address: int, data: int) -> None:
        for start, end, device in self.devices:
            if address < start or address > end: continue
            return device.write(address - start, bytes([data & 0xFF]))
        raise ValueError(f"Address {address:08x} out of bounds")

    def read(self, address: int, amount: int) -> bytes:
        if amount < 512:
            data = []
            for i in range(amount):
                data.append(self.read_single(address+i))
            return bytes(data)

        for start, end, device in self.devices:
            if address < start or address > end: continue
            return device.read(address-start, amount)

    def write(self, address: int, data: bytes) -> None:
        if len(data) < 512:
            for i,b in enumerate(data):
                self.write_single(address+i, b)
            return
        for start, end, device in self.devices:
            if address < start or address > end: continue
            return device.write(address-start, data)
        raise ValueError(f"Address {address:08x} out of bounds")
