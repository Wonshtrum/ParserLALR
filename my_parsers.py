from parser import Parser, production
from lrk import NT


Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
class ParserMath(Parser):
	START = Add
	@production(Add, "+", Factor, out=Add)
	def _(a, _1, f):
		return [a, "+", f]
	@production(Add, "-", Factor, out=Add)
	def _(a, _1, f):
		return [a, "-", f]
	@production(Factor, "*", Term, out=Factor)
	def _(f, _1, t):
		return [f, "*", t]
	@production(Factor, "/", Term, out=Factor)
	def _(f, _1, t):
		return [f, "/", t]
	@production("(", Add, ")", out=Term)
	def _(_1, a, _2):
		return a
	@production("num", out=Term)
	def _(_1):
		return _1
	@production(Factor, out=Add)
	def _(_1):
		return _1
	@production(Term, out=Factor)
	def _(_1):
		return _1


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
