from lalr.lexer import Lexer, token
from lalr.parser import Parser, production, NT
from lalr.utils import Node


class LexerGlop(Lexer):
	ENTRIES = [
		"function", "var", "while", "return", "RET",
		"=", ";", ",", "(", ")", "{", "}", "[", "]", "+", "-", "*", "/"
	]

	@token("[<=>]={0,1}")
	def _(self, val):
		return val, "cmp"
	@token("[a-zA-Z_][a-zA-Z0-9_]*")
	def _(self, val):
		return val, "id"
	@token("([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)")
	def _(self, val):
		return float(val), "num"
	@token("[ \t\r\n]+")
	def _(self, val):
		pass
	@token("/\*.*?\*/", priority=1)
	def _(self, val):
		pass
	@token("/\*", priority=1)
	def _(self, val):
		raise self.raise_error(f'Start of Multiline comment without closing "*/"', 2)


Instructions = NT("Instructions")
Instruction = NT("Instruction")
Statements = NT("Statements")
Statement = NT("Statement")
Arguments = NT("Arguments")
Argument = NT("Argument")
List = NT("List")

Declaration = NT("Declaration")
Assignment = NT("Assignment")
Return = NT("Return")

Expression = NT("Expression")
Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
class ParserGlop(Parser):
	START = Instructions

	@production("function", "id", "(", Arguments, ")", Statement, out=Instruction)
	def _(_1, name, _2, args, _3, body):
		return Node("func", name, args, body)

	@production("var", "id", "=", Expression, out=Declaration)
	def _(_1, name, _2, value):
		return Node("decl", name, value)
	@production("id", "(", List, ")", out=Term)
	def _(name, _1, args, _2):
		return Node("call", name, args)
	@production("id", "=", Expression, out=Assignment)
	def _(location, _1, value):
		return Node("set", location, value)
	@production("return", Expression, out=Return)
	def _(_1, value):
		return Node("ret", value)

	@production("id", out=Arguments)
	def _(arg):
		return Node("args", arg)
	@production(Arguments, ",", "id", out=Arguments)
	def _(args, _1, arg):
		return args.add(arg)
	@production(Expression, out=List)
	def _(value):
		return Node("list", value)
	@production(List, ",", Expression, out=List)
	def _(values, _1, value):
		return values.add(value)
	@production(Statements, Statement, out=Statements)
	def _(statements, statement):
		return statements.add(statement)
	@production(Statement, out=Statements)
	def _(statement):
		return Node("stmts", statement)
	@production(Instruction, out=Instructions)
	def _(instruction):
		return Node("prog", instruction)
	@production(Instructions, Instruction, out=Instructions)
	def _(instructions, instruction):
		return instructions.add(instruction)

	@production(Declaration, ";", out=Statement)
	def _(_1, _2):
		return _1
	@production(Assignment, ";", out=Statement)
	def _(_1, _2):
		return _1
	@production(Return, ";", out=Statement)
	def _(_1, _2):
		return _1
	@production(Expression, ";", out=Statement)
	def _(_1, _2):
		return _1
	@production("{", "}", out=Statement)
	def _(_1, _2):
		return Node("<empty>")
	@production("{", Statements, "}", out=Statement)
	def _(_1, _2, _3):
		return _2
	@production("while", "(", Expression, ")", Statement, out=Statement)
	def _(_1, _2, cond, _3, body):
		return Node("while", cond, body)
	@production(Statement, out=Instruction)
	def _(statement):
		return statement

	@production(Expression, "cmp", Add, out=Expression)
	def _(expression, op, add):
		return Node(op, expression, add)
	@production(Add, "+", Factor, out=Add)
	def _(add, _1, factor):
		return Node("+", add, factor)
	@production(Add, "-", Factor, out=Add)
	def _(add, _1, factor):
		return Node("-", add, factor)
	@production(Factor, "*", Term, out=Factor)
	def _(factor, _1, term):
		return Node("*", factor, term)
	@production(Factor, "/", Term, out=Factor)
	def _(factor, _1, term):
		return Node(factor, "/", term)
	@production("(", Expression, ")", out=Term)
	def _(_1, expression, _2):
		return expression

	@production("num", out=Term)
	def _(_1):
		return _1
	@production("id", out=Term)
	def _(_1):
		return _1
	@production("-", Term, out=Term)
	def _(_1, term):
		if isinstance(t, float):
			return -term
		return Node("-", term)
	@production("+", Term, out=Term)
	def _(_1, term):
		return term

	@production(Add, out=Expression)
	def _(_1):
		return _1
	@production(Factor, out=Add)
	def _(_1):
		return _1
	@production(Term, out=Factor)
	def _(_1):
		return _1


GLexer = LexerGlop
GParser = ParserGlop


if __name__ == "__main__":
	text = """
function test(a, b) {
	/* comment */
	var i = a;
	while (i < /* inline */ b) {
		/*
		multiline
		*/
		print(i);
		i = i+1;
	}
	return a+b;
}

test(2, test(1, 1));
"""[1:]
	lexer = LexerGlop(text)
	tokens, error = lexer.tokens()
	if error:
		print(error)
	else:
		print(tokens)
		result, error = ParserGlop.parse(tokens, lexer)
		if error:
			print(error)
		else:
			print(text)
			print(result)
