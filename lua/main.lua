local cpu = require("devices/cpu/init").cpu
local ram = require("devices/memory/ram").ram
local bus = require("devices/memory/address_bus").addressbus
local logger = require("utils/logger").logger

local RAM_RANGE = {0x80000000, 0x84000000}

local LOGGER = logger.init(9)
local RAM = ram.init(RAM_RANGE[2] - RAM_RANGE[1])
local BUS = bus.init({RAM_RANGE[1], RAM_RANGE[2], RAM})
local CPU = cpu.init(LOGGER, BUS)

CPU:run()