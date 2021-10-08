from lrk import Rules, unroll, parse


def production(*tokens, out="S"):
	class deco:
		def __init__(self, method):
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
	ENTRIES = None
	@classmethod
	def build(cls):
		if cls.ENTRIES is None:
			cls.ENTRIES = []
		rules = Rules(*cls.ENTRIES)
		rules, goto, states = unroll(rules, cls.START)
		cls.ENTRIES = goto
	
	@classmethod
	def parse(cls, tokens):
		return parse(cls.ENTRIES, tokens)
