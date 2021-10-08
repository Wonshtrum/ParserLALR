from lrk import EOF
from errors import Illegal_Token
import re


class Token:
	def __init__(self, value, type=None, lexer=None):
		self.value = value
		self.type = value if type is None else type
		if lexer is not None:
			self.line = lexer.line
			self.pos = lexer.pos
			self.pos_nl = lexer.pos_nl
			self.pos_end = lexer.pos_end

	def __repr__(self):
		if self.value == self.type:
			return f'Token({repr(self.type)})'
		return f'Token({repr(self.type)}, {repr(self.value)})'

	def __str__(self):
		return self.__repr__()


DEFAULT_PRIORITY = 0
def token(pattern, priority=DEFAULT_PRIORITY):
	class deco:
		def __init__(self, f):
			def wrapper(lexer, val):
				result = f(lexer, val)
				if result is None:
					return None
				elif isinstance(result, tuple):
					return Token(result[0], result[1], lexer)
				else:
					return Token(result, result, lexer)
			entry = (re.compile(pattern, re.DOTALL), wrapper, priority)
			token.entries.append(entry)

		def __set_name__(self, owner, name):
			if owner.ENTRIES is None:
				owner.ENTRIES = token.entries
			else:
				owner.ENTRIES.extend(token.entries)
			owner.build()
			token.entries = []

	return deco

token.entries = []


class Lexer:
	ENTRIES = None
	@classmethod
	def build(cls):
		if cls.ENTRIES is None:
			cls.ENTRIES = []
		for i, entry in enumerate(cls.ENTRIES):
			if isinstance(entry, tuple):
				cls.ENTRIES[i] = cls.expand(*entry)
			else:
				cls.ENTRIES[i] = cls.expand(entry)
		cls.ENTRIES.sort(key=lambda entry:-entry[2])

	@classmethod
	def expand(cls, pattern, wrapper=None, priority=DEFAULT_PRIORITY):
		if isinstance(pattern, str):
			pattern = re.compile(re.escape(pattern))
			type = wrapper
			wrapper = lambda lexer, x: Token(x, type, lexer) 
		return pattern, wrapper, priority

	def __init__(self, text, file_name="<stdin>"):
		self.file_name = file_name
		self.text = text
		self.view = text
		self.line = 1
		self.pos = 0
		self.pos_nl = 0
		self.pos_end = 0

	def advance(self, token):
		n = len(token)
		self.view = self.view[n:]
		self.pos += n
		n = token.count("\n")
		if n:
			self.line += n
			after, _, before = token[::-1].partition("\n")
			self.pos_nl = self.pos - len(after)

	def raise_error(self, msg, size=1):
		raise Illegal_Token(msg, self.file_name, self.text, self, size)

	def tokens(self):
		stream = []
		try:
			while self.view:
				current = None
				for pattern, wrapper, priority in self.ENTRIES:
					m = pattern.match(self.view)
					if m and (current is None or current[0].end() < m.end()):
						current = (m, wrapper)
				if current is None:
					print(stream)
					self.raise_error(f'Illegal character: "{self.view[0]}"')
				m, wrapper = current
				self.pos_end += m.end()
				result = wrapper(self, m.group())
				self.advance(m.group())
				if result is not None:
					stream.append(result)
			stream.append(Token(EOF, lexer=self))
		except Illegal_Token as error:
			return None, error.format_error()
		return stream, None

	def __repr__(self):
		return "\n".join(f"- {pattern}, {priority}" for pattern, wrapper, priority in self.ENTRIES)

	def __str__(self):
		return self.__repr__()
