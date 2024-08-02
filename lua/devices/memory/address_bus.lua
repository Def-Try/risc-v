local addressbus = {}

local bit = require("bit")

local function deepcopy(obj, seen)
    seen = seen or {}
    if obj == nil then return nil end
    if seen[obj] then return seen[obj] end
    local new_obj = {}
    seen[obj] = new_obj
    setmetatable(new_obj, deepcopy(getmetatable(obj), seen))
    for key, value in next, obj, nil do
        key = (type(key) == 'table') and deepcopy(key, seen) or key
        value = (type(value) == 'table') and deepcopy(value, seen) or value
        new_obj[key] = value
    end
    return new_obj
end

function addressbus.init(devices)
    local this = deepcopy(addressbus)
    this.devices = devices
    return this
end

function addressbus:read_single(address)
    for _, device in ipairs(self.devices) do
        local start, end_, dev = device[1], device[2], device[3]
        if not (address < start or address > end_) then
            read = string.byte(dev:read(address - start, 1))
            return bit.band(read, 0xFF)
        end
    end
    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

function addressbus:write_single(address, data)
    for _, device in ipairs(self.devices) do
        local start, end_, dev = device[1], device[2], device[3]
        if not (address < start or address > end_) then
            write = dev:write(address - start, string.char(bit.band(data, 0xFF)))
            return
        end
    end
    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

function addressbus:read(address, amount)
    if amount < 512 then
        local data = {}
        for i=0,amount-1 do
            data[i+1] = string.char(self:read_single(address + i))
        end
        return table.concat(data)
    end

    for _, device in ipairs(self.devices) do
        local start, end_, dev = device[1], device[2], device[3]
        if not (address < start or address > end_) then
            return dev:read(address - start, 1)
        end
    end

    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

function addressbus:write(address, data)
    if #data < 512 then
        for i=0,#data-1 do
            self:write_single(address + i, data:byte(i+1))
        end
        return
    end

    for _, device in ipairs(self.devices) do
        local start, end_, dev = device[1], device[2], device[3]
        if not (address < start or address > end_) then
            dev:write(address - start, data)
            return
        end
    end

    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

return {addressbus=addressbus}