bit = require("utils.bit")

function mkbitrepr(i,bc)
  bc=bc or 32
  local bitrepr = ""
  for x=0,bc-1 do
    bitrepr = bit.pick(i, x)..bitrepr
  end
  return bitrepr
end

i=bit.bnot(0b00001111)
print(i..": "..mkbitrepr(i))

