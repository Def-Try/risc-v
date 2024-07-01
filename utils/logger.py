class Logger:
	def __init__(self, level):
		self.textlog = ""
		self.level = level
		self.enabled = True
	def log(self, level, who, message):
		if not self.enabled: return
		text = f"[L{level} / {who}] {message}"
		self.textlog += text+"\n"
		if self.level >= level:
			print(text)
