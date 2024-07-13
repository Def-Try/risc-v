local bit32 = require("bit")

local INSTRUCTIONS = require("devices/cpu/instructions")

local PROFILING_MODE = false

local cpu = {
	registers = {pc=0},
	integer_registers = {
		-1, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0,
	}
}

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


function cpu.init(logger, bus)
	local this = deepcopy(cpu)
	this.bus = bus
	this.logger = logger
	this.registers.pc = 0x80000000
	if PROFILING_MODE then
	    this.profiling_data = {}
	end
	return this
end

function cpu:int_read(reg)
	if reg == 0 then return 0 end -- x0 always returns 0
	return self.integer_registers[reg]
end

function cpu:int_write(reg, val)
	if reg == 0 then return end -- x0 is hardwired
	self.integer_registers[reg] = val
end


function cpu:get_instruction(instn)
    local instruction = INSTRUCTIONS[instn]
    if instruction then
        self.logger:log(8, "CPU", string.format("Instruction implemented: %02x / %x / %s", instn, instn, instruction.__name or ''))
        return instruction
    end
    error(string.format("Instruction not implemented: %02x / %d", instn, instn))
end

local function bytes_to_int_little(str)
    local n = 0
    for k=1, string.len(str) do
        n = n + string.byte(str, k) * 2 ^ ((k - 1) * 8)
    end
    return n
end

function cpu:fetch_instruction()
    local fetched = bit32.band(bytes_to_int_little(self.bus:read(self.registers["pc"], 2)), 0xffff)
    local inst_size = 16

    if bit32.band(fetched, 0x7F) == 0xF then        -- (80+16nnn)-bit instruction
        local n = bit32.band(bit32.rshift(fetched, 12), 0x7)
        if n == 0x7 then                            -- >= 192 bit instruction
            error("Instruction size not implemented: " .. string.format("%04x", fetched) .. " / " .. string.format("%016b", fetched))
        end
        local x = bit32.band(bit32.rshift(fetched, 7), 0x1F)
        inst_size = 80 + 16 * n
        fetched = bit32.band(bit32.bor(0, bytes_to_int_little(self.bus:read(self.registers["pc"], math.floor(inst_size / 8)))), 0xffffffffffffffff)
    elseif bit32.band(fetched, 0x7F) == 0x2F then   -- 64 bit instruction
        fetched = bit32.band(bytes_to_int_little(self.bus:read(self.registers["pc"], 8)), 0xffffffffffffffff)
        inst_size = 64
    elseif bit32.band(fetched, 0x2F) == 0x1F then   -- 48 bit instruction
        fetched = bit32.band(bytes_to_int_little(self.bus:read(self.registers["pc"], 6)), 0xffffffffffff)
        inst_size = 48
    elseif bit32.band(fetched, 0x2) == 0x2 then     -- 32 bit instruction
        fetched = bit32.band(bytes_to_int_little(self.bus:read(self.registers["pc"], 4)), 0xffffffff)
        inst_size = 32
    else                                            -- 16 bit instruction
        -- we already have 16 bit, skip that
    end

    self.logger:log(8, "CPU", "############## fetched: " .. string.format("%08x", fetched) .. " at PC " .. string.format("%08x", self.registers["pc"]))
    if inst_size == 32 then
        local instruction = bit32.band(fetched, 0x7F)
        local instruct = self:get_instruction(instruction)
        instruct.inst_size = inst_size
        return instruct, fetched
    else
        error("Instruction format not implemented: " .. string.format("%016x", fetched) .. " / inst_s " .. inst_size)
    end
end

function cpu:run(instruction_cb)
    local graceful_exit = false
    while true do
        local instruction, fetched = self:fetch_instruction()
        if not instruction then break end

        instruction_cb()
        local start_time = os.clock()
        local jumped_pc = instruction(fetched, self, self.bus, self.logger)
        local took = os.clock() - start_time

        self.integer_registers[0] = 0
        for i = 1, #self.integer_registers do
            self.integer_registers[i] = bit32.band(self.integer_registers[i], 0xFFFFFFFF)
        end

        if not jumped_pc then
            self.registers["pc"] = self.registers["pc"] + math.floor(instruction.inst_size / 8)
        end
        if self.profiling_data then
            if not self.profiling_data[instruction.serialized] then
                self.profiling_data[instruction.serialized] = {}
            end
            table.insert(self.profiling_data[instruction.serialized], took)
        end
    end

    if not graceful_exit then
        return -1
    end
end

return {cpu=cpu}