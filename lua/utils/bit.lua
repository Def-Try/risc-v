local bit = {}
bit.bitcount = 32

function bit.rshift(num, n) return math.max(0, math.floor(num / 2^n)) end
function bit.lshift(num, n) return num * 2^n end
function bit.pick(num, n) return bit.rshift(num, n) % 2 end

function bit.min_bits(num) return
    for i = bit.bitcount-1, 0 do
        if bit.pick(num, i) == 1 then return i+1 end
    end
    return 1
end

function bit.bor(n1, n2)
    local final = 0
    for i=bit.bitcount-1,0,-1 do
        final = bit.lshift(final +
            math.ceil((bit.pick(n1, i) + bit.pick(n2, i)) / 2), 1)
    end
    return bit.rshift(final, 1)
end
function bit.bxor(n1, n2)
    local final = 0
    for i=bit.bitcount-1,0,-1 do
        final = bit.lshift(final +
            math.ceil(bit.pick(n1, i) + bit.pick(n2, i))%2, 1)
    end
    return bit.rshift(final, 1)
end
function bit.band(n1, n2)
    local final = 0
    for i=bit.bitcount-1,0,-1 do
        final = bit.lshift(final +
            math.floor((bit.pick(n1, i) + bit.pick(n2, i))/2), 1)
    end
    return bit.rshift(final, 1)
end
function bit.bnot(n)
    local final = 0
    for i=bit.bitcount-1,0,-1 do
        final = bit.lshift(final + (bit.pick(n, i)==1 and 0 or 1), 1)
    end
    return bit.rshift(final, 1)
end

return bit
