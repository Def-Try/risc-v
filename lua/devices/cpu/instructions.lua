local bit = require("bit")

local decoder = require("utils/decoder")
local converter = require("utils/converter")

local decoders = {
    J=decoder.decode_J_type,
    I=decoder.decode_I_type,
    R=decoder.decode_R_type,
    Ra=decoder.decode_R_type_atomic,
    U=decoder.decode_U_type,
    B=decoder.decode_B_type,
    S=decoder.decode_S_type
}

local function jal()
	local _ = {}
	_.mt = {}
	_.mt.__call = function(z_, data, CPU, BUS, LOGGER)
		local drg, val = decoders['J'](data)
        --local next_instruction = bit.band(CPU.registers["pc"] + 4, 0xFFFFFFFF)
        local next_instruction = CPU.registers["pc"] + 4
        local val = converter.interpret_as_21_bit_signed_value(val)
        CPU.registers["pc"] = CPU.registers["pc"] + val
        CPU:int_write(drg, next_instruction)
        print(string.format("%08x", CPU.registers["pc"]))
        -- CPU.registers["pc"] = bit.band(CPU.registers["pc"], 0xFFFFFFFF)
        -- no idea why it does that, but band instead of masking away actually adds stuff
        LOGGER:log(6, "CPU", string.format("JAL -> %08x(+%d) -> x%d", CPU.registers["pc"], val, drg))
        _.serialized = 'jal'
        return true
	end
	_.__name = "JAL"
	setmetatable(_, _.mt)
	return _
end

return {
	[0x6f] = jal()
}