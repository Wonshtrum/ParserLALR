from .lrk import EOF
from .errors import Illegal_Token
from .regex import RegexGraph, to_ascii, parse_regex
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
			if f.__code__.co_argcount != 2:
				raise ValueError("Token decorator must take exactly 2 arguments")
			def wrapper(lexer, val):
				result = f(lexer, val)
				if result is None:
					return None
				elif isinstance(result, tuple):
					return Token(result[0], result[1], lexer)
				else:
					return Token(result, result, lexer)
			entry = (pattern, wrapper, priority)
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
	BACKEND = "re"
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
		cls.backend = BackendGraph if cls.BACKEND == "graph" else BackendRe
		cls.backend.build(cls)

	@classmethod
	def expand(cls, pattern, wrapper=None, priority=DEFAULT_PRIORITY):
		if wrapper is None:
			pattern = re.escape(pattern)
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
		self.backend.init(self)

	def advance(self, token):
		n = len(token)
		self.view = self.view[n:]
		self.pos += n
		n = token.count("\n")
		if n:
			self.line += n
			after, _, before = token[::-1].partition("\n")
			self.pos_nl = self.pos - len(after)

	def tokens(self):
		stream = []
		try:
			while self.view:
				result = self.backend.get_token(self)
				if result is None:
					print(stream)
					self.raise_error(f'Illegal character: "{self.text[self.pos]}"')
				token, wrapper = result
				self.pos_end += len(token)
				result = wrapper(self, token)
				self.advance(token)
				if result is not None:
					stream.append(result)
			stream.append(Token(EOF, lexer=self))
		except Illegal_Token as error:
			return None, error.format_error()
		return stream, None

	def raise_error(self, msg, size=1, note=None):
		raise Illegal_Token(msg, self.file_name, self.text, self, size, note)

	def __repr__(self):
		return "\n".join(f"- {pattern}, {priority}" for pattern, wrapper, priority in self.ENTRIES)

	def __str__(self):
		return self.__repr__()


class Backend:
	@staticmethod
	def build(lexer):
		pass
	@staticmethod
	def init(lexer):
		pass
	@staticmethod
	def get_token(lexer):
		pass


class BackendRe(Backend):
	@staticmethod
	def init(lexer):
		lexer.ENTRIES = [(re.compile(pattern, re.DOTALL), wrapper, priority) for pattern, wrapper, priority in lexer.ENTRIES]

	@staticmethod
	def get_token(lexer):
		current = None
		for pattern, wrapper, priority in lexer.ENTRIES:
			m = pattern.match(lexer.view)
			if m and (current is None or current[0].end() < m.end()):
				current = (m, wrapper)
		if current is None:
			return current
		m, wrapper = current
		return m.group(), wrapper


class BackendGraph(Backend):
	@staticmethod
	def build(lexer):
		lexer.GRAPH = RegexGraph(*[parse_regex(entry[0]) for entry in lexer.ENTRIES])
		lexer.GRAPH.compile()

	@staticmethod
	def init(lexer):
		lexer.view = to_ascii(lexer.view)

	@staticmethod
	def get_token(lexer):
		m = lexer.GRAPH.match(lexer.view)
		if m is None:
			return m
		token = lexer.text[lexer.pos:lexer.pos+m.length]
		wrapper = lexer.ENTRIES[m.families[0].id][1]
		return token, wrapper
