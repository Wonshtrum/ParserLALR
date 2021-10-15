from lalr.utils import node_print, member_getter as default_getter
from lalr.errors import ParserError
from types import GeneratorType as generator


def decompile(e):
	over = lambda params, symbol: symbol.join(decompile(_) for _ in params)
	if e.type is Expression.NOP:
		return "..."
	if e.type is Expression.STRING:
		return f'"{e.string}"';
	if e.type is Expression.NUMBER:
		return f"{e.number}"
	if e.type is Expression.IDENT:
		return e.ident.name
	if e.type is Expression.ADD:
		return over(e.params, "+")
	if e.type is Expression.NEG:
		return f"-({decompile(e.params[0])})"
	if e.type is Expression.EQ:
		return over(e.params, "==")
	if e.type is Expression.COR:
		return over(e.params, " || ")
	if e.type is Expression.CAND:
		return over(e.params, " && ")
	if e.type is Expression.LOOP:
		return f"while({decompile(e.params[0])}){{{over(e.params[1:],';')};}}"
	if e.type is Expression.ADDROF:
		return f"*({decompile(e.params[0])})"
	if e.type is Expression.DEREF:
		return f"&({decompile(e.params[0])})"
	if e.type is Expression.FCALL:
		return f"{decompile(e.params[0])}({over(e.params[1:],',')})"
	if e.type is Expression.COPY:
		return f"{decompile(e.params[1])}={decompile(e.params[0])}"
	if e.type is Expression.COMMA:
		return f"({over(e.params,',')},)"
	if e.type is Expression.RET:
		return f"return {decompile(e.params[0])}"


def member_getter(node):
	if isinstance(node, Context):
		return None, [("tempcounter", node.tempcounter), ("fun", node.fun.name), ("func_list", [_.name for _ in node.func_list]), ("scopes", node.scopes)]
	elif isinstance(node, Program):
		return None, [(None, _) for _ in node.instructions]
	elif isinstance(node, Function):
		return f"Function: {node.name}", [(None, node.code)]
	elif isinstance(node, Identifier):
		return f"IDENT {node.type[0].upper()}{node.index}: {node.name}", None
	elif not isinstance(node, Expression):
		return default_getter(node)
	elif node.type is Expression.NOP:
		return "NOP", None
	elif node.type is Expression.STRING:
		return f"STRING: {node.string}", None
	elif node.type is Expression.NUMBER:
		return f"NUMBER: {node.number}", None
	elif node.type is Expression.IDENT:
		return member_getter(node.ident)
	elif node.type is Expression.FCALL:
		return f"CALL({node.params[0]})", [(None, _) for _ in node.params[1:]]
	elif node.type is Expression.COPY:
		return "COPY", [("from", node.params[0]), ("to", node.params[1])]
	else:
		return node.type.upper(), [(None, _) for _ in node.params]


class Beautiful:
	def __repr__(self):
		return node_print(None, self, member_getter)


def pre_param(f, *args):
	def wrapper(*params):
		return f(*args, *params)
	return wrapper


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
				return expr(scope[name])
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
		fun.code = e_comma(code, e_ret(0))
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
	def __init__(self, type, name, index=0):
		self.type = type
		self.name = name
		self.index = index


for n in Identifier.ENUM:
	locals()[f"id_{n}"] = pre_param(Identifier, n)
	locals()[f"is_{n}"] = pre_param(lambda n, e: e.type is n, n)


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
		self.params = [] if params is None else [Expression.constructor(param) for param in params]

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
		if len(params) == 1:
			if isinstance(params[0], list):
				return Expression(n, params=params[0])
			elif isinstance(params[0], generator):
				return Expression(n, params=list(params[0]))
		return Expression(n, params=list(params))

	def assign(self, other):
		return Expression(Expression.COPY, params=[other, self])

	def add(self, *others):
		for other in others:
			self.params.append(Expression.constructor(other))
		return self

	def set(self, arg):
		new = Expression.constructor(arg)
		self.type = new.type
		self.ident = new.ident
		self.string = new.string
		self.number = new.number
		self.params = new.params

	def copy(self):
		return Expression(self.type, self.ident, self.string, self.number, [_.copy() for _ in self.params])

	def is_pure(self):
		if not self.params:
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

	def get_const(self):
		if self.type is Expression.NUMBER:
			return self
		elif self.type is Expression.STRING:
			return self
		elif self.type is Expression.COPY:
			return self.params[0].get_const()
		elif self.type is Expression.COMMA:
			return self.params[-1].get_const()
		else:
			return None

	def __eq__(self, other):
		return self.type is other.type and self.ident is other.ident and self.string == other.string and self.number == other.number and self.params == other.params


for n in Expression.ENUM:
	locals()[f"e_{n}"]  = pre_param(Expression.sub_constructor, n)
	locals()[f"is_{n}"] = pre_param(lambda n, e: e.type is n, n)
expr = Expression.constructor
is_true  = lambda e: is_number(e) and e.number != 0
is_false = lambda e: is_number(e) and e.number == 0


class Function(Beautiful):
	def __init__(self, name, code, num_vars=0, num_params=0):
		self.name = name
		self.code = code
		self.num_vars = num_vars
		self.num_params = num_params
		self.pure = False
		self.pure_known = False

	def temp(self):
		self.num_vars += 1
		return expr(id_variable(f"$C{self.num_vars-1}", self.num_vars-1))

	def default():
		return Function("<empty>", e_nop())


class Program(Beautiful):
	def __init__(self, *instructions):
		self.instructions = list(instructions)

	def add(self, instruction):
		self.instructions.append(instruction)
		return self
