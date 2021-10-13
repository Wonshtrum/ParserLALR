from lalr.utils import member_getter, node_print
from lalr.errors import ParserError


class Beautiful:
	def __repr__(self):
		return node_print(None, self, member_getter)


def create_sub_constructor(constructor, n):
	def sub_constructor(*params):
		return constructor(n, *params)
	return sub_constructor


class Context(Beautiful):
	def __init__(self):
		self.scopes = [{}]
		self.func_list = []
		self.fun = Function.default()
		self.tempcounter = 0;

	def define(self, name, ident):
		if name in self.scopes[-1]:
			raise ParserError(f'NameError: Duplicate definition of "{name}"')
		self.scopes[-1][name] = ident
		return ident

	def use(self, name):
		for scope in reversed(self.scopes):
			if name in scope:
				return Expression(scope[name])
		raise ParserError(f'NameError: Undefined identifier "{name}"')

	def defvar(self, name):
		self.fun.num_vars += 1
		return expr(self.define(name, id_variable(name, self.fun.num_vars-1)))

	def defun(self, name):
		self.fun.name = name
		return expr(self.define(name, id_function(name, len(self.func_list))))

	def defparam(self, name):
		self.fun.num_params += 1
		return expr(self.define(name, id_parameter(name, self.fun.num_params-1)))

	def temp(self):
		self.tempcounter += 1
		return expr(self.defvar(f"$I{self.tempcounter-1}"))

	def add_function(self, code):
		fun = self.fun
		fun.code = e_comma(*code.params, e_ret(0))
		self.func_list.append(fun)
		self.fun = Function.default()
		return fun

	def push(self):
		self.scopes.append({})

	def pop(self):
		self.scopes.pop()


class Identifier(Beautiful):
	UNDEFINED = "undefined"
	PARAMETER = "parameter"
	FUNCTION = "function"
	VARIABLE = "variable"
	ENUM = (UNDEFINED, PARAMETER, FUNCTION, VARIABLE)
	def __init__(self, type, name, index=None):
		self.type = type
		self.name = name
		self.index = index


for n in Identifier.ENUM:
	locals()[f"id_{n}"] = create_sub_constructor(Identifier, n)


class Expression(Beautiful):
	NOP = "nop"
	STRING = "string"
	NUMBER = "number"
	IDENT = "ident"
	ADD = "add"
	NEG = "neg"
	EQ = "eq"
	COR = "cor"
	CAND = "cand"
	LOOP = "loop"
	ADDROF = "addrof"
	DEREF = "deref"
	FCALL = "fcall"
	COPY = "copy"
	COMMA = "comma"
	RET = "ret"
	ENUM = (NOP, STRING, NUMBER, IDENT, ADD, NEG, EQ, COR, CAND, LOOP, ADDROF, DEREF, FCALL, COPY, COMMA, RET)
	def __init__(self, type, ident=None, string=None, number=None, params=None):
		self.type = type
		self.ident = ident
		self.string = string
		self.number = number
		self.params = None if params is None else [Expression.constructor(param) for param in params]

	def constructor(arg=None):
		if arg is None:
			return Expression()
		elif isinstance(arg, Expression):
			return arg
		elif isinstance(arg, Identifier):
			return Expression(Expression.IDENT, ident=arg)
		elif isinstance(arg, str):
			return Expression(Expression.STRING, string=arg)
		elif isinstance(arg, int):
			return Expression(Expression.NUMBER, number=arg)
		else:
			raise ValueError(f"Can't construct expression with {arg}")

	def sub_constructor(n, *params):
		return Expression(n, params=list(params))

	def assign(self, other):
		return Expression(Expression.COPY, params=[other, self])

	def add(self, *others):
		for other in others:
			self.params.append(Expression.constructor(other))
		return self

	def copy(self):
		return Expression(self.type, self.ident, self.number, self.params)

	def is_pure(self):
		if self.params is None:
			return True
		if self.type is Expression.FCALL:
			return False
		elif self.type is Expression.COPY:
			return False
		elif self.type is Expression.RET:
			return False
		elif self.type is Expression.LOOP:
			return False
		for param in self.params:
			if not param.is_pure():
				return False
		return True


for n in Expression.ENUM:
	locals()[f"e_{n}"] = create_sub_constructor(Expression.sub_constructor, n)
expr = Expression.constructor


class Function(Beautiful):
	def __init__(self, name, code, num_vars=0, num_params=0):
		self.name = name
		self.code = code
		self.num_vars = num_vars
		self.num_params = num_params

	def default():
		return Function("<master>", e_nop())


class Program(Beautiful):
	def __init__(self, *instructions):
		self.instructions = list(instructions)

	def add(self, instruction):
		self.instructions.append(instruction)
		return self
