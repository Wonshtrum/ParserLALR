from lalr.lexer import Lexer, token
from lalr.parser import Parser, production, NT


class LexerMath(Lexer):
	ENTRIES = ["+", "-", "*", "/", "(", ")"]
	@token("([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)")
	def _(self, val):
		return float(val), "num"


Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
class ParserMath(Parser):
	START = Add
	@production(Add, "+", Factor, out=Add)
	def _(a, _1, f):
		return a, "+", f
	@production(Add, "-", Factor, out=Add)
	def _(a, _1, f):
		return a, "-", f
	@production(Factor, "*", Term, out=Factor)
	def _(f, _1, t):
		return f, "*", t
	@production(Factor, "/", Term, out=Factor)
	def _(f, _1, t):
		return f, "/", t
	@production("(", Add, ")", out=Term)
	def _(_1, a, _2):
		return a
	@production("num", out=Term)
	def _(_1):
		return _1
	@production("-", Term, out=Term)
	def _(_1, t):
		if isinstance(t, float):
			return -t
		return ("-", t)
	@production("+", Term, out=Term)
	def _(_1, t):
		return t
	@production(Factor, out=Add)
	def _(_1):
		return _1
	@production(Term, out=Factor)
	def _(_1):
		return _1


if __name__ == "__main__":
	text = "-(1-1)*1+1*(1-1-1*2-1)"
	lexer = LexerMath(text)
	tokens, error = lexer.tokens()
	print(text)
	if error:
		print(error)
	else:
		print(tokens)
		result, error = ParserMath.parse(tokens, lexer)
		if error:
			print(error)
		else:
			print(result)
