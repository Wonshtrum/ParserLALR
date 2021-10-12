from .lrk import Rules, NT, unroll, parse, group


def production(*tokens, out=None):
	if out is None:
		raise ValueError("Production rule can't produce None")
	class deco:
		def __init__(self, method):
			argcount = method.__code__.co_argcount
			if argcount == len(tokens):
				old = method
				method = lambda parser, *args: old(*args)
			elif argcount != len(tokens)+1:
				raise ValueError("Production rule must have the same number of arguments as left tokens")
			entry = (out, tokens, method)
			production.entries.append(entry)

		def __set_name__(self, owner, name):
			if owner.ENTRIES is None:
				owner.ENTRIES = production.entries
			else:
				owner.ENTRIES.extend(production.entries)
			owner.build()
			production.entries = []

	return deco

production.entries = []


class Parser:
	START = "S"
	MINIFY = False
	ENTRIES = None
	@classmethod
	def build(cls):
		if cls.ENTRIES is None:
			cls.ENTRIES = []
		rules = Rules(*cls.ENTRIES)
		rules, goto, states = unroll(rules, cls.START, cls.MINIFY)
		cls.ENTRIES = goto

	@classmethod
	def print(cls, level=0):
		grouped = group(cls.ENTRIES)
		for s in sorted(grouped.keys()):
			if level == 0:
				print(s, ":", tuple(grouped[s].keys()))
			elif level == 1:
				print(s, ":", {k:(v[0] if isinstance(v, tuple) else v) for k, v in grouped[s].items()})
			else:
				print(s, ":", grouped[s])
		print(len(grouped.keys()))

	def get_context(self):
		return self

	def get_execution_context(self):
		return []

	def parse(self, tokens, lexer):
		return parse(self.ENTRIES, tokens, lexer, self.get_context())
