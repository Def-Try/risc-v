local bit32 = require("bit")

local Decoder = {}

function Decoder.decode_I_type(instruction)
    local instruction_subtype = Decoder.get_subtype__funct3(instruction)
    local destination_reg = Decoder.get_destination_register__rd(instruction)
    local source_reg = Decoder.get_source_register__rs1(instruction)
    local immediate_val = Decoder.get_hardcoded_number__immediate_i(instruction)

    return instruction_subtype, destination_reg, source_reg, immediate_val
end

function Decoder.decode_J_type(instruction)
    local destination_reg = Decoder.get_destination_register__rd(instruction)
    local immediate_val = Decoder.get_hardcoded_number__immediate_j(instruction)

    return destination_reg, immediate_val
end

function Decoder.decode_U_type(instruction)
    local destination_reg = Decoder.get_destination_register__rd(instruction)
    local immediate_val = Decoder.get_hardcoded_number__immediate_u(instruction)

    return destination_reg, immediate_val
end

function Decoder.decode_B_type(instruction)
    local instruction_subtype = Decoder.get_subtype__funct3(instruction)
    local source_reg_1 = Decoder.get_source_register__rs1(instruction)
    local source_reg_2 = Decoder.get_source_register__rs2(instruction)
    local immediate_val = Decoder.get_hardcoded_number__immediate_b(instruction)

    return instruction_subtype, source_reg_1, source_reg_2, immediate_val
end

function Decoder.decode_S_type(instruction)
    local instruction_subtype = Decoder.get_subtype__funct3(instruction)
    local source_reg_1 = Decoder.get_source_register__rs1(instruction)
    local source_reg_2 = Decoder.get_source_register__rs2(instruction)
    local immediate_val = Decoder.get_hardcoded_number__immediate_s(instruction)

    return instruction_subtype, source_reg_1, source_reg_2, immediate_val
end

function Decoder.decode_R_type(instruction)
    local instruction_subtype_f3 = Decoder.get_subtype__funct3(instruction)
    local instruction_subtype_f7 = Decoder.get_subtype__funct7(instruction)
    local source_reg_1 = Decoder.get_source_register__rs1(instruction)
    local source_reg_2 = Decoder.get_source_register__rs2(instruction)
    local destination_reg = Decoder.get_destination_register__rd(instruction)

    return instruction_subtype_f3, instruction_subtype_f7, source_reg_1, source_reg_2, destination_reg
end

function Decoder.decode_R_type_atomic(instruction)
    local instruction_subtype_f3 = Decoder.get_subtype__funct3(instruction)
    local instruction_subtype_f5 = Decoder.get_subtype__funct5(instruction)
    local source_reg_1 = Decoder.get_source_register__rs1(instruction)
    local source_reg_2 = Decoder.get_source_register__rs2(instruction)
    local destination_reg = Decoder.get_destination_register__rd(instruction)

    return instruction_subtype_f3, instruction_subtype_f5, source_reg_1, source_reg_2, destination_reg
end

function Decoder.get_subtype__funct3(instruction)
    local val = bit32.band(instruction, 0b00000000000000000111000000000000)
    val = bit32.rshift(val, 12)
    return val
end

function Decoder.get_subtype__funct5(instruction)
    local val = bit32.rshift(instruction, 27)
    return val
end

function Decoder.get_subtype__funct7(instruction)
    local val = bit32.rshift(instruction, 25)
    return val
end

function Decoder.get_source_register__rs1(instruction)
    local val = bit32.band(instruction, 0b00000000000011111000000000000000)
    return bit32.rshift(val, 15)
end

function Decoder.get_source_register__rs2(instruction)
    local val = bit32.band(instruction, 0b00000001111100000000000000000000)
    return bit32.rshift(val, 20)
end

function Decoder.get_destination_register__rd(instruction)
    local val = bit32.band(instruction, 0b00000000000000000000111110000000)
    return bit32.rshift(val, 7)
end

function Decoder.get_hardcoded_number__immediate_i(instruction)
    return bit32.rshift(instruction, 20)
end

function Decoder.get_hardcoded_number__immediate_u(instruction)
    return bit32.rshift(instruction, 12)
end

function Decoder.get_hardcoded_number__immediate_j(instruction)
    local instruction_bits_31_31 = bit32.band(instruction, 0b10000000000000000000000000000000)
    local instruction_bits_30_21 = bit32.band(instruction, 0b01111111111000000000000000000000)
    local instruction_bits_20_20 = bit32.band(instruction, 0b00000000000100000000000000000000)
    local instruction_bits_19_12 = bit32.band(instruction, 0b00000000000011111111000000000000)

    immediate_bits_20_20 = bit32.rshift(instruction_bits_31_31, 11)
    immediate_bits_19_12 = instruction_bits_19_12
    immediate_bits_11_11 = bit32.rshift(instruction_bits_20_20, 9)
    immediate_bits_10_01 = bit32.rshift(instruction_bits_30_21, 20)
    immediate_bits_00_00 = 0

    val = immediate_bits_20_20 or 0
    val = bit32.bor(bit32.lshift(val, 12), instruction_bits_19_12)
    val = bit32.bor(bit32.lshift(val, 5), immediate_bits_11_11)
    val = bit32.bor(bit32.lshift(val, 11), immediate_bits_10_01)

    return val
end

function Decoder.get_hardcoded_number__immediate_b(instruction)
    local instruction_bits_31_31 = bit32.band(instruction, 0b10000000000000000000000000000000)
    local instruction_bits_30_25 = bit32.band(instruction, 0b01111110000000000000000000000000)
    local instruction_bits_11_08 = bit32.band(instruction, 0b00000000000000000000111100000000)
    local instruction_bits_07_07 = bit32.band(instruction, 0b00000000000000000000000010000000)

    immediate_bits_12_12 = bit32.rshift(instruction_bits_31_31, 19)
    immediate_bits_11_11 = bit32.lshift(bit32.band(instruction_bits_07_07, 0b000000000000000000001111), 4)
    immediate_bits_10_05 = bit32.rshift(instruction_bits_30_25, 20)
    immediate_bits_04_01 = bit32.rshift(instruction_bits_11_08, 7)
    immediate_bits_00_00 = 0

    val = bit32.bor(bit32.bor(immediate_bits_12_12, immediate_bits_11_11), immediate_bits_10_05)
    val = bit32.bor(val, immediate_bits_04_01)

    return val
end

function Decoder.get_hardcoded_number__immediate_s(instruction)
    local instruction_bits_31_25 = bit32.band(instruction, 0b11111110000000000000000000000000)
    local instruction_bits_11_07 = bit32.band(instruction, 0b00000000000000000000111110000000)

    immediate_bits_11_05 = bit32.rshift(instruction_bits_31_25, 20)
    immediate_bits_04_00 = bit32.rshift(instruction_bits_11_07, 7)

    return bit32.bor(bit32.lshift(immediate_bits_11_05, 5), immediate_bits_04_00)
end

return Decoder