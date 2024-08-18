local bit = require("bit")

local converter = {
    -- convert signed value to 32-bit signed value
    interpret_as_32_bit_signed_value = function(signed_value)
        local ret_val = signed_value
        if bit.band(signed_value, 0x80000000) ~= 0 then
            ret_val = -((bit.lshift(bit.band(bit.bnot(signed_value), 0xFFFFFFFF), 1) + 1))
        end
        return ret_val
    end,

    -- convert signed value to 20-bit signed value
    interpret_as_20_bit_signed_value = function(signed_value)
        local ret_val = signed_value
        if bit.band(signed_value, 0x00080000) ~= 0 then
            ret_val = -((bit.lshift(bit.band(bit.bnot(signed_value), 0x000FFFFF), 5) + 1))
        end
        return ret_val
    end,

    -- convert signed value to 21-bit signed value
    interpret_as_21_bit_signed_value = function(signed_value)
        local ret_val = signed_value
        if bit.band(signed_value, 0x00100000) ~= 0 then
            ret_val = -((bit.lshift(bit.band(bit.bnot(signed_value), 0x000FFFFF), 6) + 1))
        end
        return ret_val
    end,

    -- convert signed value to 13-bit signed value
    interpretAs13BitSignedValue = function(signed_value)
        local ret_val = signed_value
        if bit.band(signed_value, 0x00001000) ~= 0 then
            ret_val = -((bit.lshift(bit.band(bit.bnot(signed_value), 0x00000FFF), 4) + 1))
        end
        return ret_val
    end,

    -- convert signed value to 12-bit signed value
    interpretAs12BitSignedValue = function(signed_value)
        local ret_val = signed_value
        if bit.band(signed_value, 0x00000800) ~= 0 then
            ret_val = -((bit.lshift(bit.band(bit.bnot(signed_value), 0x00000FFF), 4) + 1))
        end
        return ret_val
    end,

    -- convert value to 32-bit unsigned value
    convertTo32BitUnsignedValue = function(value)
        return value
    end,

    -- sign extend 12-bit value to 32-bit value
    signExtend12BitValue = function(value)
        if bit.band(value, 0x800) ~= 0 then
            value = bor(value, 0xFFFFF000)
        end
        return value
    end,

    -- convert signed value to 12-bit signed value
    interpretAs12BitUnsignedValue = function(unsigned_value)
        local ret_val = unsigned_value
        if bit.band(unsigned_value, 0x800) ~= 0 then
            ret_val = -((bit.lshift(bit.band(bit.bnot(unsigned_value), 0x00000FFF), 4) + 1))
        end
        return ret_val
    end,
}

return converter
