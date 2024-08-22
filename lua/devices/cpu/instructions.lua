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

local function immediate_functions()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
		local sub, drg, srg, imm = decoders['J'](data)
        imm = converter.interpret_as_12_bit_signed_value(val)
        if sub == 0x0 then -- addi
            CPU.int_write(drg, CPU.int_read(srg) + imm)
        elseif sub == 0x4 then -- xori
            CPU.int_write(drg, bit.bxor(CPU.int_read(srg), imm))
        elseif sub == 0x6 then -- ori
            CPU.int_write(drg, bit.bor(CPU.int_read(srg), imm))
        elseif sub == 0x7 then -- andi
            CPU.int_write(drg, bit.band(CPU.int_read(srg), imm))
        end
    end
    _.__name = "IMM"
    setmetatable(_, _.mt)
    return _
end

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
    [0x13] = immediate_functions(),
	[0x6f] = jal(),
}