TAB = "  "
SPACES_IN_TAB = 4
class Illegal_Token(Exception):
	def __init__(self, msg, file_name, text, pos, size=None, note=None):
		self.msg = msg.replace("\t", TAB)
		self.file_name = file_name
		self.text = text
		self.pos = pos
		self.size = max(1, pos.pos_end-pos.pos) if size is None else size
		self.note = note

	def format_error(self):
		line, *_ = self.text[self.pos.pos_nl:].partition("\n")
		pos_ln = self.pos.pos-self.pos.pos_nl
		tabs = line[:pos_ln].count("\t")
		padding = pos_ln + tabs*(SPACES_IN_TAB-1)
		line = line.replace("\t", " "*SPACES_IN_TAB)
		result = f"""
{TAB}File "{self.file_name}", line {self.pos.line}
{TAB}{self.msg}
{TAB}{TAB}{line}
{TAB}{TAB}{" "*padding}{"^"*self.size}"""+("" if self.note is None else f"""
{TAB}note: {self.note}""")
		return result[1:]
