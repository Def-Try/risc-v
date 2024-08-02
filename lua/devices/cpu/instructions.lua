local INSTRUCTIONS = {
    [111]=(function() -- jal (1101111) (J-type)
        local instruction
        function instruction(fetched, cpu, addressbus, logger)
            -- TODO: a
        end
        -- instruction.__name = "jal"
        return instruction
    end)()
}

return INSTRUCTIONS