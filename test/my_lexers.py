from lalr.lexer import Lexer, token


class LexerMath(Lexer):
	ENTRIES = ["+", "-", "*", "/", "(", ")"]

	@token("[-+]?([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)")
	def _(self, val):
		return float(val), "num"


class LexerJSON(Lexer):
	ENTRIES = ["{", "}", "[", "]", ",", ":"]

	@token("[-+]?([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)")
	def _(self, val):
		return float(val), "num"
	@token('"(\\"|[^"])*?"')
	def _(self, val):
		return val[1:-1], "str"
	@token('\'(\\"|[^"])*?\'')
	def _(self, val):
		return val[1:-1], "str"
	@token("true")
	def _(self, val):
		return True, "bool"
	@token("false")
	def _(self, val):
		return False, "bool"
	@token("[ \t\r\n]+")
	def _(self, val):
		pass


class LexerGlop(Lexer):
	ENTRIES = [
		("function",    "FUNC"),
		("var",         "VAR"),
		("while",       "LOOP"),
		("return",      "RET"),
		"=", ";", ",", "(", ")", "{", "}", "[", "]", "+", "-", "*", "/"
	]

	@token("[<=>]={0,1}")
	def _(self, val):
		return val, "CMP"
	@token("[a-zA-Z_][a-zA-Z0-9_]*")
	def _(self, val):
		return val, "ID"
	@token("[-+]?([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)")
	def _(self, val):
		return float(val), "FLOAT"
	@token("[ \t\r\n]+")
	def _(self, val):
		pass
	@token("/\*.*?\*/", priority=1)
	def _(self, val):
		pass
	@token("/\*", priority=1)
	def _(self, val):
		raise self.raise_error(f'Start of Multiline comment without closing "*/"', 2)
