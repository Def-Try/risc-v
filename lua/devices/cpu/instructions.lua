local bit = require("utils/bit")

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
        local sub, drg, srg, imm = decoders['I'](data)
        imm = converter.interpret_as_12_bit_signed_value(val)
        if sub == 0x0 then -- addi
            LOGGER:log(6, "CPU", string.format("ADDI -> x%d = x%d + %d", drg, srg, imm))
            CPU:int_write(drg, CPU:int_read(srg) + imm)
            _.serialized = 'addi'
            return
        elseif sub == 0x2 then -- slti
            LOGGER:log(6, "CPU", string.format("SLTI -> x%d = x%d < %d", drg, srg, imm))
            imm = converter.interpret_as_32_bit_signed_value(converter.sign_extend_12_bit_value(imm))
            CPU:int_write(drg, converter.interpret_as_32_bit_signed_value(CPU:int_read(srg)) < imm and 1 or 0)
            _.serialized = 'slti'
            return
        elseif sub == 0x4 then -- xori
            LOGGER:log(6, "CPU", string.format("XORI -> x%d = x%d ^ %08x", drg, srg, imm))
            CPU:int_write(drg, bit.bxor(CPU:int_read(srg), imm))
            _.serialized = 'xori'
            return
        elseif sub == 0x6 then -- ori
            LOGGER:log(6, "CPU", string.format("ORI -> x%d = x%d | %08x", drg, srg, imm))
            CPU:int_write(drg, bit.bor(CPU:int_read(srg), imm))
            _.serialized = 'ori'
            return
        elseif sub == 0x7 then -- andi
            LOGGER:log(6, "CPU", string.format("ANDI -> x%d = x%d & %08x", drg, srg, imm))
            CPU:int_write(drg, bit.band(CPU:int_read(srg), imm))
            _.serialized = 'andi'
            return
        end
        error("anyimm: subinst no impl: "..sub)
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
        CPU.registers["pc"] = CPU.registers["pc"] % 0xFFFFFFFF
        LOGGER:log(6, "CPU", string.format("JAL -> %08x(+%d) -> x%d", CPU.registers["pc"], val, drg))
        _.serialized = 'jal'
        return true
    end
    _.__name = "JAL"
    setmetatable(_, _.mt)
    return _
end

local function ebccsr()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
    local ist, drg, srg, val = decoders['I'](data)
        --local next_instruction = bit.band(CPU.registers["pc"] + 4, 0xFFFFFFFF)
        if ist == 0 then
            error("EBCCSR: ist=0")
        end
        if ist == 1 then
            LOGGER:log(6, "CPU", string.format("CSR-RW x%s x%s %s", srg, drg, val))
            local cur_val, new_val = CPU:csr_read(val), CPU:int_read(srg)
            CPU:csr_write(val, new_val)
            CPU:int_write(drg, cur_val)
            _.serialized = 'csrrw'
            return
        end
        if ist == 2 then
            LOGGER:log(6, "CPU", string.format("CSR-RS x%s x%s %s", srg, drg, val))
            local cur_val = CPU:csr_read(val)
            local new_val = bit.bor(cur_val, CPU:int_read(srg))
            CPU:csr_write(val, new_val)
            CPU:int_write(drg, cur_val)
            _.serialized = 'csrrs'
            return
        end
        if ist == 3 then
            LOGGER:log(6, "CPU", string.format("CSR-RC x%s x%s %s", srg, drg, val))
            local cur_val = CPU:csr_read(val)
            local new_val = bit.band(cur_val, bit.bnot(CPU:int_read(srg)))
            CPU:csr_write(val, new_val)
            CPU:int_write(drg, cur_val)
            _.serialized = 'csrrc'
            return
        end
        if ist == 5 then
            LOGGER:log(6, "CPU", string.format("CSR-RWI %s x%s %s", srg, drg, val))
            local cur_val = CPU:csr_read(val)
            local new_val = srg
            CPU:csr_write(val, new_val)
            CPU:int_write(drg, cur_val)
            _.serialized = 'csrrwi'
            return
        end
        if ist == 7 then
            LOGGER:log(6, "CPU", string.format("CSR-RCI %s x%s %s", srg, drg, val))
            local cur_val = CPU:csr_read(val)
            local new_val = bit.band(cur_val, bit.bnot(srg))
            CPU:csr_write(val, new_val)
            CPU:int_write(drg, cur_val)
            _.serialized = 'csrrxi'
            return
        end
        error("ebccsr: subinst no impl: "..ist)
    end
    _.__name = "EBCCSR"
    setmetatable(_, _.mt)
    return _
end

local function fence()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
        LOGGER:log(6, "CPU", "FENCE")
        _.serialized = 'fence'
    end
    _.__name = "FENCE"
    setmetatable(_, _.mt)
    return _
end

local function lui()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
        local drg, val = decoders['U'](data)
        LOGGER:log(6, "CPU", string.format("LUI x%d = %d", drg, converter.interpret_as_20_bit_signed_value(val)))
        CPU:int_write(drg, (bit.lshift(val, 12)))
        _.serialized = 'lui'
    end
    _.__name = "LUI"
    setmetatable(_, _.mt)
    return _
end

local function jalr()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
        local ist, drg, srg, val = decoders['I'](data)
        local next_instruction = CPU.registers["pc"] + 4
        val = converter.interpret_as_12_bit_signed_value(val)
        CPU.registers["pc"] = (CPU:int_read(srg) + val) % 0xFFFFFFFF + 1
        CPU:int_write(drg, next_instruction)
        LOGGER:log(6, "CPU", string.format("JALR -> %08x(x%d + %d) -> x%d", CPU.registers["pc"], srg, val, drg))
        _.serialized = 'jalr'
        return true
    end
    _.__name = "JALR"
    setmetatable(_, _.mt)
    return _
end

local function auipc()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
        local drg, val = decoders['U'](data)
        val = converter.interpret_as_20_bit_signed_value(val)
        CPU:int_write(drg, CPU.registers["pc"] + bit.lshift(val, 12))
        LOGGER:log(6, "CPU", string.format("AUIPC -> x%d = PC + %d", drg, bit.lshift(val, 12)))
        _.serialized = 'auipc'
        return
    end
    _.__name = "AUIPC"
    setmetatable(_, _.mt)
    return _
end

local function branch()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
        local ist, srg1, srg2, val = decoders['B'](data)
        local uv1, uv2 = CPU:int_read(srg1), CPU:int_read(srg2)
        local sv1, sv2 = converter.interpret_as_32_bit_signed_value(uv1), converter.interpret_as_32_bit_signed_value(uv2)
        local jmp = converter.interpret_as_13_bit_signed_value(val)
        local jmpd = false

        if ist == 4 then -- blt
            if sv1 < sv2 then
                CPU.registers["pc"] = (CPU.registers["pc"] + jmp) % 0xFFFFFFFF + 1
                jmpd = true
                LOGGER:log(6, "CPU", string.format("BLT -> x%d < x%d ==> PC + %d", srg1, srg2, jmp))
            else
                LOGGER:log(6, "CPU", string.format("BLT -> x%d < x%d =/> PC + %d", srg1, srg2, jmp))
            end
            _.serialized = 'blt'
            return jmpd
        end

        if ist == 5 then -- bge
            if sv1 >= sv2 then
                CPU.registers["pc"] = (CPU.registers["pc"] + jmp) % 0xFFFFFFFF + 1
                jmpd = true
                LOGGER:log(6, "CPU", string.format("BGE -> x%d >= x%d ==> PC + %d", srg1, srg2, jmp))
            else
                LOGGER:log(6, "CPU", string.format("BGE -> x%d >= x%d =/> PC + %d", srg1, srg2, jmp))
            end
            _.serialized = 'bge'
            return jmpd
        end

        error("branch: subinst no impl: "..ist)
    end
    _.__name = "BRANCH"
    setmetatable(_, _.mt)
    return _
end

local function store()
    local _ = {}
    _.mt = {}
    _.mt.__call = function(z_, data, CPU, BUS, LOGGER)
        local ist, srg1, srg2, val = decoders['S'](data)
        val = converter.interpret_as_12_bit_signed_value(val)
        local addr = (CPU:int_read(srg1) + val) % 0xFFFFFFFF + 1
        data = CPU:int_read(srg2)

        if ist == 2 then
            LOGGER:log(6, "CPU", string.format("SW -> x%d -> x%d + %d", srg2, srg1, val))
            data = (data % 0xFFFFFFFF)
            BUS:write(addr, string.char(data % 256)..string.char(data / 256 % 256)..string.char(data / 256*2 % 256)..string.char(data / 256*3 % 256))
            _.serialized = 'sw'
            return
        end

        error("store: subinst no impl: "..ist)
    end
    _.__name = "STORE"
    setmetatable(_, _.mt)
    return _
end

return {
    [0x13] = immediate_functions(),
    [0x6f] = jal(),
    [0x73] = ebccsr(),
    [0x0f] = fence(),
    [0x37] = lui(),
    [0x67] = jalr(),
    [0x17] = auipc(),
    [0x63] = branch(),
    [0x23] = store()
}
