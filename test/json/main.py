from lalr.lexer import Lexer, token
from lalr.parser import Parser, production, NT
from time import time


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
GLexer = LexerJSON


KV = NT("KV")
KVS = NT("KVS")
JSON = NT("JSON")
List = NT("List")
Element = NT("Element")
Elements = NT("Elements")
class ParserJSON(Parser):
	START = JSON

	@production("str", ":", Element, out=KV)
	def _(k, _1, v):
		return k, v
	@production("{", KVS, "}", out=JSON)
	def _(_1, kvs, _2):
		return dict(kvs)
	@production("[", Elements, "]", out=List)
	def _(_1, le, _2):
		return le
	@production("{", "}", out=JSON)
	def _(_1, _2):
		return {}
	@production("[", "]", out=List)
	def _(_1, _2):
		return []
	@production(KV, out=KVS)
	def _(kv):
		return [kv]
	@production(KV, ",", KVS, out=KVS)
	def _(kv, _1, kvs):
		return [kv]+kvs
	@production(Element, out=Elements)
	def _(e):
		return [e]
	@production(Element, ",", Elements, out=Elements)
	def _(e, _1, le):
		return [e]+le
	@production(JSON, out=Element)
	def _(_1):
		return _1
	@production(List, out=Element)
	def _(_1):
		return _1
	@production("str", out=Element)
	def _(_1):
		return _1
	@production("num", out=Element)
	def _(_1):
		return _1
	@production("bool", out=Element)
	def _(_1):
		return _1
GParser = ParserJSON


if __name__ == "__main__":
	text = open("data.json", "r").read()
	lexer = LexerJSON(text)
	tokens, error = lexer.tokens()
	if error:
		print(error)
	else:
		t = time()
		result, error = ParserJSON.parse(tokens, lexer)
		if error:
			print(error)
		else:
			print(result)
		print(time()-t)
