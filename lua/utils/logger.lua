local logger = {}

local function deepcopy(obj, seen)
    seen = seen or {}
    if obj == nil then return nil end
    if seen[obj] then return seen[obj] end
    local new_obj = {}
    seen[obj] = new_obj
    setmetatable(new_obj, deepcopy(getmetatable(obj), seen))
    for key, value in next, obj, nil do
        key = (type(key) == 'table') and deepcopy(key, seen) or key
        value = (type(value) == 'table') and deepcopy(value, seen) or value
        new_obj[key] = value
    end
    return new_obj
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