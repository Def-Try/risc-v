local logger = {}

local function deepcopy(o, seen)
  seen = seen or {}
  if o == nil then return nil end
  if seen[o] then return seen[o] end
  local no = {}
  seen[o] = no
  setmetatable(no, deepcopy(getmetatable(o), seen))
  for k, v in next, o, nil do
    k = (type(k) == 'table') and deepcopy(k, seen) or k
    v = (type(v) == 'table') and deepcopy(v, seen) or v
    no[k] = v
  end
  return no
end

function logger.init(level)
    local this = deepcopy(logger)
    this.textlog = ""
    this.level = level or 1 
    this.enabled = true
    return this
end

function logger:log(level, who, message)
    if not self.enabled then return end
    local text = string.format("[L%d / %s] %s", level, who, message)
    self.textlog = self.textlog .. text .. "\n"
    if self.level >= level then
        print(text)
    end
end

return {logger=logger}