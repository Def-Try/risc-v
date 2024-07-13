local RAM_BYTEARRAY = {}

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

function RAM_BYTEARRAY.init(size)
    local this = deepcopy(RAM_BYTEARRAY)
    this.memory = {}
    this.size = size
    for i=0,size do
        this.memory[i] = 0
    end
    return this
end

function RAM_BYTEARRAY:write(to_addr, data)
    if to_addr + #data > self.size then
        error(string.format("MemoryError: Invalid memory address or size (addr %08x + datasize %08x (%08x) > size %08x)", to_addr, #data, to_addr + #data, self.size))
    end
    for i=1,#data do
        self.memory[to_addr+i-1] = data:byte(i)
    end
end

function RAM_BYTEARRAY:read(from_addr, amount)
    if amount == 1 then
        if from_addr < 0 or from_addr > self.size then
            error("MemoryError: Invalid memory address")
        end
        return string.char(self.memory[from_addr] or 0)
    else
        local result = ""
        for i=from_addr,from_addr+amount-1 do
            if i < 0 or i > self.size then
                error("MemoryError: Invalid memory address")
            end
            result = result .. string.char(self.memory[i] or 0)
        end
        return result
    end
end

return {ram=RAM_BYTEARRAY}