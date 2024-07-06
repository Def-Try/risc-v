local addressbus = {}

local bit = require("bit")

local function deepcopy(o, seen)
  seen = seen or {}
  if o == nil then return nil end
  if seen[o] then return seen[o] end
  local no = {}
  seen[o] = no
  setmetatable(no, deepcopy(getmetatable(o), seen))
  for k, v in next, o, nil do
    k = (type(k) == 'table') and deepcopy(k, seen) or k
    v = (type(v) == 'table') and deepcopy(v, seen) or v
    no[k] = v
  end
  return no
end

function addressbus.init(devices)
    local this = deepcopy(addressbus)
    this.devices = devices
    return this
end

function addressbus:read_single(address)
    for _, device in ipairs(self.devices) do
        local start, end_, read = device:bounds()
        if address < start or address > end_ then goto continue end
        read = device:read(address - start, 1)
        return bit.band(read, 0xFF)
        ::continue::
    end
    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

function addressbus:write_single(address, data)
    for _, device in ipairs(self.devices) do
        local start, end_, write = device:bounds()
        if address < start or address > end_ then goto continue end
        write = device:write(address - start, string.pack("B", bit.band(data, 0xFF)))
        return
        ::continue::
    end
    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

function addressbus:read(address, amount)
    if amount < 512 then
        local data = {}
        for i=0,amount-1 do
            data[i+1] = self:read_single(address + i)
        end
        return table.concat(data)
    end

    for _, device in ipairs(self.devices) do
        local start, end_, read = device:bounds()
        if address < start or address > end_ then goto continue end
        return read(address - start, amount)
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
        local start, end_, write = device:bounds()
        if address < start or address > end_ then goto continue end
        write(address - start, data)
        return
    end

    error("ValueError: Address " .. string.format("%08x", address) .. " out of bounds")
end

return {addressbus=addressbus}