from lalr.lexer import Lexer, token
from lalr.parser import Parser, production, NT
from .ast import *


class LexerBisqwit(Lexer):
	ENTRIES = [
		"if", "else", "while", "return", "var", "func",
		"=", ",", ";", "?", ":", "&",
		"{", "}", "(", ")", "[", "]",
		"+", "-", "*", "/", "%",
		"++", "--",
		"-=", "+=", "*=", "/=", "%=",
		"==", "!=", "<", ">", ">=", "<=",
		"true", "false", "&&", "||", "!",
	]

	@token("[a-zA-Z_][a-zA-Z0-9_]*")
	def _(self, val):
		return val, "id"
	@token('"(\\"|[^"])*?"')
	def _(self, val):
		return val[1:-1], "str"
	@token("[0-9]+")
	def _(self, val):
		return int(val), "num"

	@token("[ \t\r\n]+")
	def _(self, val):
		pass
	@token("//.*?(\n|$)", priority=1)
	def _(self, val):
		pass
	@token("/\*.*?\*/", priority=1)
	def _(self, val):
		pass
	@token("/\*", priority=1)
	def _(self, val):
		raise self.raise_error(f'Start of Multiline comment without closing "*/"', 2)


CommaExpression = NT("CommaExpression")
FullExpression = NT("FullExpression")
Expression1 = NT("Expression1")
Expression2 = NT("Expression2")
Expression3 = NT("Expression3")
Expression4 = NT("Expression4")
Expression5 = NT("Expression5")
Expression6 = NT("Expression6")
Expression7 = NT("Expression7")
Expression8 = NT("Expression8")
Expression9 = NT("Expression9")

Statements = NT("Statements")
Statement = NT("Statement")
FunctionStart = NT("FunctionStart")
Functions = NT("Functions")
Function = NT("Function")
Instructions = NT("Instructions")
Instruction = NT("Instruction")

Declarations = NT("Declarations")
Declaration = NT("Declaration")
NameList = NT("NameList")
class ParserBisqwit(Parser):
	START = Instructions
	#MINIFY = True

	def __init__(self):
		self.context = Context()

	def get_context(self):
		return self.context

	@production("id", out=NameList)
	def _(ctx, name):
		ctx.defparam(name)
	@production(NameList, ",", "id", out=NameList)
	def _(ctx, names, _1, name):
		ctx.defparam(name)

	@production("func", "id", out=FunctionStart)
	def _(ctx, _1, name):
		ctx.defun(name)
		ctx.push()
		return ctx.fun
	@production(FunctionStart, "(", NameList, ")", Statement, out=Function)
	def _(ctx, _1, _2, arguments, _3, body):
		fun = ctx.add_function(body)
		ctx.pop()
		return fun
	@production(FunctionStart, "(", ")", Statement, out=Function)
	def _(ctx, _1, _2, _3, body):
		fun = ctx.add_function(body)
		ctx.pop()
		return fun

	@production(Function, out=Instruction)
	def _(function):
		return function
	@production(Statement, out=Instruction)
	def _(statement):
		return statement
	@production(Instruction, out=Instructions)
	def _(instruction):
		return Program(instruction)
	@production(Instructions, Instruction, out=Instructions)
	def _(instructions, instruction):
		return instructions.add(instruction)

	@production("{", out=Statements)
	def _(ctx, _1):
		ctx.push()
		return e_comma()
	@production(Statements, Statement, out=Statements)
	def _(statements, statement):
		return statements.add(statement)
	@production(Statements, "}", out=Statement)
	def _(ctx, statements, _2):
		ctx.pop()
		return statements
	@production("if", "(", FullExpression, ")", Statement, out=Statement)
	def _(_1, _2, condition, _3, thencase):
		return e_cand(condition, thencase)
	@production("while", "(", FullExpression, ")", Statement, out=Statement)
	def _(_1, _2, condition, _3, body):
		return e_loop(condition, body)
	@production("return", FullExpression, ";", out=Statement)
	def _(_1, expression, _2):
		return e_ret(expression)
	@production(FullExpression, ";", out=Statement)
	def _(expression, _2):
		return expression
	"""@production(";", out=Statement)
	def _(_1):
		return"""

	@production("id", "=", Expression1, out=Declaration)
	def _(ctx, name, _1, value):
		return ctx.defvar(name).assign(value)
	@production("id", out=Declaration)
	def _(ctx, name):
		return ctx.defvar(name).assign(0)
	@production(Declaration, out=Declarations)
	def _(declaration):
		return e_comma(declaration)
	@production(Declarations, ",", Declaration, out=Declarations)
	def _(declarations, _1, declaration):
		return declarations.add(declaration)

	@production(Expression1, out=CommaExpression)
	def _(e):
		return e_comma(e)
	@production(CommaExpression, ",", Expression1, out=CommaExpression)
	def _(l, _1, r):
		return l.add(r)
	@production(CommaExpression, out=FullExpression)
	def _(e):
		return e
	@production("var", Declarations, out=FullExpression)
	def _(_1, declarations):
		return declarations

	@production(Expression2, "?", Expression1, ":", Expression1, out=Expression1)
	def _(ctx, condition, _1, thencase, _2, elsecase):
		i = ctx.temp()
		return e_comma(e_cor(e_cand(condition, e_comma(i.assign(thencase), 1)), i.assign(elsecase)), i)
	@production(Expression2, "=", Expression1, out=Expression1)
	def _(l, _1, r):
		return l.assign(r)
	@production(Expression2, "+=", Expression1, out=Expression1)
	def _(ctx, l, _1, r):
		if not l.is_pure():
			tmp = ctx.temp()
			left = tmp.assign(e_addrof(l))
			l = e_deref(tmp)
			return e_comma(left, l.assign(e_add(l, r)))
		return l.assign(e_add(l, r))

	@production(Expression2, "-=", Expression1, out=Expression1)
	def _(ctx, l, _1, r):
		r = e_neg(r)
		if not l.is_pure():
			tmp = ctx.temp()
			left = tmp.assign(e_addrof(l))
			l = e_deref(tmp)
			return e_comma(left, l.assign(e_add(l, r)))
		return l.assign(e_add(l, r))
	"""@production(Expression2, "*=", Expression1, out=Expression1)
	def _(l, _1, r):
		return
	@production(Expression2, "/=", Expression1, out=Expression1)
	def _(l, _1, r):
		return
	@production(Expression2, "%=", Expression1, out=Expression1)
	def _(l, _1, r):
		return"""
	@production(Expression2, out=Expression1)
	def _(e):
		return e

	@production(Expression2, "||", Expression3, out=Expression2)
	def _(l, _1, r):
		return e_cor(l, r)
	@production(Expression3, out=Expression2)
	def _(e):
		return e

	@production(Expression3, "&&", Expression4, out=Expression3)
	def _(l, _1, r):
		return e_cand(l, r)
	@production(Expression4, out=Expression3)
	def _(e):
		return e

	@production(Expression4, "==", Expression5, out=Expression4)
	def _(l, _1, r):
		return e_eq(l, r)
	@production(Expression4, "!=", Expression5, out=Expression4)
	def _(l, _1, r):
		return e_eq(e_eq(l, r), 0)
	"""@production(Expression4, "<", Expression5, out=Expression4)
	def _(l, _1, r):
		return
	@production(Expression4, ">", Expression5, out=Expression4)
	def _(l, _1, r):
		return
	@production(Expression4, "<=", Expression5, out=Expression4)
	def _(l, _1, r):
		return
	@production(Expression4, ">=", Expression5, out=Expression4)
	def _(l, _1, r):
		return"""
	@production(Expression5, out=Expression4)
	def _(e):
		return e

	@production(Expression5, "+", Expression6, out=Expression5)
	def _(l, _1, r):
		return e_add(l, r)
	@production(Expression5, "-", Expression6, out=Expression5)
	def _(l, _1, r):
		return e_add(l, e_neg(r))
	@production(Expression6, out=Expression5)
	def _(e):
		return e

	"""@production(Expression6, "*", Expression7, out=Expression6)
	def _(l, _1, r):
		return
	@production(Expression6, "/", Expression7, out=Expression6)
	def _(l, _1, r):
		return
	@production(Expression6, "%", Expression7, out=Expression6)
	def _(l, _1, r):
		return"""
	@production(Expression7, out=Expression6)
	def _(e):
		return e

	@production("&", Expression7, out=Expression7)
	def _(_1, e):
		return e_addrof(e)
	@production("*", Expression7, out=Expression7)
	def _(_1, e):
		return e_deref(e)
	@production("!", Expression7, out=Expression7)
	def _(_1, e):
		return e_eq(e, 0)
	@production("-", Expression7, out=Expression7)
	def _(_1, e):
		return e_neg(e)
	@production("++", Expression7, out=Expression7)
	def _(ctx, _1, e):
		if not e.is_pure():
			tmp = ctx.temp()
			left = tmp.assign(e_addrof(e))
			e = e_deref(tmp)
			return e_comma(left, e.assign(e_add(e, 1)))
		return e.assign(e_add(e, 1))
	@production("--", Expression7, out=Expression7)
	def _(ctx, _1, e):
		if not e.is_pure():
			tmp = ctx.temp()
			left = tmp.assign(e_addrof(e))
			e = e_deref(tmp)
			return e_comma(left, e.assign(e_add(e, -1)))
		return e.assign(e_add(e, -1))
	@production(Expression8, out=Expression7)
	def _(e):
		return e

	@production(Expression8, "++", out=Expression8)
	def _(ctx, e, _1):
		left = e_nop()
		if not e.is_pure():
			tmp1 = ctx.temp()
			left = tmp1.assign(e_addrof(e))
			e = e_deref(tmp1)
		tmp2 = ctx.temp()
		return e_comma(left, tmp2.assign(e), e.assign(e_add(e, 1)), tmp2)
	@production(Expression8, "--", out=Expression8)
	def _(ctx, e, _1):
		left = e_nop()
		if not e.is_pure():
			tmp1 = ctx.temp()
			left = tmp1.assign(e_addrof(e))
			e = e_deref(tmp1)
		tmp2 = ctx.temp()
		return e_comma(left, tmp2.assign(e), e.assign(e_add(e, -1)), tmp2)
	@production("(", FullExpression, ")", out=Expression8)
	def _(_1, e, _2):
		return e
	@production(Expression8, "[", FullExpression, "]", out=Expression8)
	def _(p, _1, i, _2):
		return e_deref(e_add(p, i))
	@production(Expression8, "(", ")", out=Expression8)
	def _(name, _1, _2):
		return e_fcall(name)
	@production(Expression8, "(", CommaExpression, ")", out=Expression8)
	def _(name, _1, args, _2):
		return e_fcall(id_function(name)).add(*args.params)
	@production("id", out=Expression8)
	def _(ctx, name):
		return ctx.use(name)
	@production("str", out=Expression8)
	def _(string):
		return expr(string)
	@production("num", out=Expression8)
	def _(number):
		return expr(number)
