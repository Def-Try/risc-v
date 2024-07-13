local cpu = require("devices/cpu/init").cpu
local ram = require("devices/memory/ram").ram
local bus = require("devices/memory/address_bus").addressbus
local logger = require("utils/logger").logger

local RAM_RANGE = {0x80000000, 0x84000000}

local LOGGER = logger.init(9)
local RAM = ram.init(RAM_RANGE[2] - RAM_RANGE[1])
local BUS = bus.init({{RAM_RANGE[1], RAM_RANGE[2], RAM}})
local CPU = cpu.init(LOGGER, BUS)

LOGGER:log(1, "MAIN", "Running self-tests...")
BUS:read(RAM_RANGE[1], 1)
LOGGER:log(1, "MAIN", " BUS: RAM single read: OK")
BUS:read(RAM_RANGE[1], 512)
LOGGER:log(1, "MAIN", " BUS: RAM bulk read: OK")
BUS:write(RAM_RANGE[1], "\0")
LOGGER:log(1, "MAIN", " BUS: RAM single write: OK")
BUS:write(RAM_RANGE[1], string.rep("\0", 512))
LOGGER:log(1, "MAIN", " BUS: RAM bulk write: OK")
LOGGER:log(1, "MAIN", "Self-tests done.")

function readAll(file)
    local f = assert(io.open(file, "rb"))
    local content = f:read("*all")
    f:close()
    return content
end

LOGGER:log(1, "MAIN", "Reading linux image...")
local linux = readAll("linux/kernel.img")
LOGGER:log(1, "MAIN", "Writing linux image into RAM...")
BUS:write(RAM_RANGE[1], linux)

function PrintTable( t, indent, done )
    local Msg = print

    done = done or {}
    indent = indent or 0
    local keys = {}
    for k,_ in pairs(t) do keys[#keys+1] = k end

    table.sort( keys, function( a, b )
        if ( type( a ) == "number" and type( b ) == "number" ) then return a < b end
        return tostring( a ) < tostring( b )
    end )

    done[ t ] = true

    for i = 1, #keys do
        local key = keys[ i ]
        local value = t[ key ]
        key = ( type( key ) == "string" ) and "[\"" .. key .. "\"]" or "[" .. tostring( key ) .. "]"

        if  ( type( value ) == "table" and not done[ value ] ) then
            done[ value ] = true
            Msg(string.rep( "\t", indent )..key, ":" )
            PrintTable ( value, indent + 2, done )
            done[ value ] = nil
        else
            Msg(string.rep( "\t", indent )..key, "\t=\t", value)
        end

    end

end

CPU:run(function() end)