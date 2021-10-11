from lalr.lexer import Lexer, token
from lalr.parser import Parser, production, NT
from .ast import *


class LexerWYOOP(Lexer):
	ENTRIES = [
		"if", "else", "while", "print", "read",
		"=", ";",
		"(", ")", "{", "}",
		"+", "-", "*", "/", "%",
		"==", "!=", "<", ">", ">=", "<=",
		"true", "false", "&&", "||", "!",
	]

	@token("[a-zA-Z_][a-zA-Z0-9_]*")
	def _(self, val):
		return val, "id"
	@token('"(\\"|[^"])*?"')
	def _(self, val):
		return val[1:-1], "str"
	@token("([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)")
	def _(self, val):
		i, f = int(val), float(val)
		if i == f:
			return i, "num"
		return f, "num"

	@token("[ \t\r\n]+")
	def _(self, val):
		pass
	@token("/\*.*?\*/", priority=1)
	def _(self, val):
		pass
	@token("/\*", priority=1)
	def _(self, val):
		raise self.raise_error(f'Start of Multiline comment without closing "*/"', 2)


ArithmeticExpressionA = NT("ArithmeticExpressionA")
ArithmeticExpressionM = NT("ArithmeticExpressionM")
ArithmeticExpressionX = NT("ArithmeticExpressionX")
ArithmeticExpression = NT("ArithmeticExpression")
RelationalExpression = NT("RelationalExpression")
BooleanExpressionO = NT("BooleanExpressionO")
BooleanExpressionA = NT("BooleanExpressionA")
BooleanExpressionX = NT("BooleanExpressionX")
BooleanExpression = NT("BooleanExpression")
StatementI = NT("StatementI")
StatementC = NT("StatementC")
Statements = NT("Statements")
Statement = NT("Statement")
Lvalue = NT("Lvalue")
class ParserWYOOP(Parser):
	START = Statements
	#MINIFY = True

	@production(Statement, out=Statements)
	def _(statement):
		return StatementBlock([statement])
	@production(Statements, Statement, out=Statements)
	def _(statements, statement):
		return statements.add(statement)

	@production(StatementI, out=Statement)
	def _(statement):
		return statement
	@production(StatementC, out=Statement)
	def _(statement):
		return statement

	@production("{", "}", out=StatementC)
	def _(_1, _2):
		return StatementBlock()
	@production("{", Statements, "}", out=StatementC)
	def _(_1, statements, _2):
		return statements
	@production(Lvalue, "=", ArithmeticExpression, ";", out=StatementC)
	def _(lvalue, _1, value, _2):
		return StatementAssign(lvalue, value)
	@production("read", Lvalue, ";", out=StatementC)
	def _(_1, lvalue, _2):
		return StatementReadInt(lvalue)
	@production("print", ArithmeticExpression, ";", out=StatementC)
	def _(_1, e, _2):
		return StatementWriteInt(e)
	@production("print", "str", ";", out=StatementC)
	def _(_1, text, _2):
		return StatementWrite(text)
	@production("if", "(", BooleanExpression, ")", StatementC, "else", StatementC, out=StatementC)
	def _(_1, _2, condition, _3, thencase, _4, elsecase):
		return StatementIfThenElse(condition, thencase, elsecase)
	@production("while", "(", BooleanExpression, ")", StatementC, out=StatementC)
	def _(_1, _2, condition, _3, body):
		return StatementWhile(condition, body)

	@production("if", "(", BooleanExpression, ")", Statement, out=StatementI)
	def _(_1, _2, condition, _3, thencase):
		return StatementIfThenElse(condition, thencase)
	@production("if", "(", BooleanExpression, ")", StatementC, "else", StatementI, out=StatementI)
	def _(_1, _2, condition, _3, thencase, _4, elsecase):
		return StatementIfThenElse(condition, thencase, elsecase)
	@production("while", "(", BooleanExpression, ")", StatementI, out=StatementI)
	def _(_1, _2, condition, _3, body):
		return StatementWhile(condition, body)
	
	@production(BooleanExpressionO, out=BooleanExpression)
	def _(e):
		return e

	@production(BooleanExpressionO, "||", BooleanExpressionA, out=BooleanExpressionO)
	def _(l, _1, r):
		return BooleanExpressionOr(l, r)
	@production(BooleanExpressionA, out=BooleanExpressionO)
	def _(e):
		return e

	@production(BooleanExpressionA, "&&", BooleanExpressionX, out=BooleanExpressionA)
	def _(l, _1, r):
		return BooleanExpressionAnd(l, r)
	@production(BooleanExpressionX, out=BooleanExpressionA)
	def _(e):
		return e

	@production(RelationalExpression, out=BooleanExpressionX)
	def _(e):
		return e
	@production("true", out=BooleanExpressionX)
	def _(e):
		return BooleanExpressionTrue()
	@production("False", out=BooleanExpressionX)
	def _(e):
		return BooleanExpressionFalse()
	@production("(", BooleanExpressionO, ")", out=BooleanExpressionX)
	def _(_1, e, _2):
		return e
	@production("!", BooleanExpressionX, out=BooleanExpressionX)
	def _(_1, e):
		return BooleanExpressionNot(e)

	@production(ArithmeticExpressionA, out=ArithmeticExpression)
	def _(e):
		return e
	
	@production(ArithmeticExpressionA, "+", ArithmeticExpressionM, out=ArithmeticExpressionA)
	def _(l, _1, r):
		return ArithmeticExpressionPlus(l, r)
	@production(ArithmeticExpressionA, "-", ArithmeticExpressionM, out=ArithmeticExpressionA)
	def _(l, _1, r):
		return ArithmeticExpressionMinus(l, r)
	@production(ArithmeticExpressionM, out=ArithmeticExpressionA)
	def _(e):
		return e

	@production(ArithmeticExpressionM, "*", ArithmeticExpressionX, out=ArithmeticExpressionM)
	def _(l, _1, r):
		return ArithmeticExpressionMult(l, r)
	@production(ArithmeticExpressionM, "/", ArithmeticExpressionX, out=ArithmeticExpressionM)
	def _(l, _1, r):
		return ArithmeticExpressionDiv(l, r)
	@production(ArithmeticExpressionM, "%", ArithmeticExpressionX, out=ArithmeticExpressionM)
	def _(l, _1, r):
		return ArithmeticExpressionMod(l, r)
	@production(ArithmeticExpressionX, out=ArithmeticExpressionM)
	def _(e):
		return e

	@production("num", out=ArithmeticExpressionX)
	def _(num):
		return ArithmeticExpressionConst(num)
	@production(Lvalue, out=ArithmeticExpressionX)
	def _(lvalue):
		return lvalue
	@production("(", ArithmeticExpressionA, ")", out=ArithmeticExpressionX)
	def _(_1, e, _2):
		return e
	@production("-", ArithmeticExpressionX, out=ArithmeticExpressionX)
	def _(_1, e, _2):
		return ArithmeticExpressionNeg(e)
	
	@production(ArithmeticExpression, "==", ArithmeticExpression, out=RelationalExpression)
	def _(right, _1, left):
		return RelationalExpressionEq(right, left)
	@production(ArithmeticExpression, "!=", ArithmeticExpression, out=RelationalExpression)
	def _(right, _1, left):
		return RelationalExpressionNEq(right, left)
	@production(ArithmeticExpression, "<", ArithmeticExpression, out=RelationalExpression)
	def _(l, _1, r):
		return RelationalExpressionLT(l, r)
	@production(ArithmeticExpression, ">", ArithmeticExpression, out=RelationalExpression)
	def _(l, _1, r):
		return RelationalExpressionGT(l, r)
	@production(ArithmeticExpression, "<=", ArithmeticExpression, out=RelationalExpression)
	def _(l, _1, r):
		return RelationalExpressionLE(l, r)
	@production(ArithmeticExpression, ">=", ArithmeticExpression, out=RelationalExpression)
	def _(l, _1, r):
		return RelationalExpressionGE(l, r)
	
	@production("id", out=Lvalue)
	def _(name):
		return LocationValueVariable(name)
