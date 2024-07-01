class Logger:
	def __init__(self, level):
		self.textlog = ""
		self.level = level
	def log(self, level, who, message):
		text = f"[L{level} / {who}] {message}"
		self.textlog += text+"\n"
		if self.level >= level:
			print(text)
