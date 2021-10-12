from lalr.utils import member_getter, node_print


class Context:
	def __init__(self):
		self.values = {}


class Statement:
	def execute(self):
		pass


class StatementBlock(Statement):
	def __init__(self, statements=None):
		self.statements = [] if statements is None else statements
	def add(self, statement):
		self.statements.append(statement)
		return self
	def execute(self, context):
		for statement in self.statements:
			statement.execute(context)
	def __repr__(self):
		return node_print("prog", self, member_getter)


class StatementWrite(Statement):
	def __init__(self, text):
		self.text = text
	def execute(self, context):
		print(self.text, end="")


class StatementWriteInt(Statement):
	def __init__(self, expression):
		self.expression = expression
	def execute(self, context):
		print(self.expression.evaluate(context), end="")


class StatementReadInt(Statement):
	def __init__(self, lvalue):
		self.lvalue = lvalue
	def execute(self, context):
		self.lvalue.set(int(input()), context)


class StatementAssign(Statement):
	def __init__(self, lvalue, expression):
		self.lvalue = lvalue
		self.expression = expression
	def execute(self, context):
		self.lvalue.set(self.expression.evaluate(context), context)


class StatementWhile(Statement):
	def __init__(self, condition, body):
		self.condition = condition
		self.body = body
	def execute(self, context):
		while self.condition.evaluate(context):
			self.body.execute(context)


class StatementIfThenElse(Statement):
	def __init__(self, condition, thencase, elsecase=None):
		self.condition = condition
		self.thencase = thencase
		self.elsecase = elsecase
	def execute(self, context):
		if (self.condition.evaluate(context)):
			if self.thencase is not None:
				self.thencase.execute(context)
		else:
			if self.elsecase is not None:
				self.elsecase.execute(context)


class LocationValueVariable:
	def __init__(self, name):
		self.name = name
	def set(self, value, context):
		context.values[self.name] = value
	def evaluate(self, context):
		if self.name not in context.values:
			raise NameError(f'NameError: Undefined identifier "{self.name}"')
		return context.values[self.name]


def create_binary_operation(op, symbol=None):
	class BinaryOperation:
		def __init__(self, l, r):
			self.l = l
			self.r = r
		def evaluate(self, context):
			return op(self.l.evaluate(context), self.r.evaluate(context))
	if symbol is not None:
		BinaryOperation.__name__ = f"BinaryOperation({symbol})"
	return BinaryOperation


def create_unary_operation(op, symbol):
	class UnaryOperation:
		def __init__(self, x):
			self.x = x
		def evaluate(self, context):
			return op(self.x.evaluate(context))
	if symbol is not None:
		UnaryOperation.__name__ = f"UnaryOperation({symbol})"
	return UnaryOperation


def create_constant(value=None):
	if value is None:
		class Constant:
			def __init__(self, x):
				self.x = x
			def evaluate(self, context):
				return self.x
	else:
		class Constant:
			def evaluate(self, context):
				return value
		Constant.__name__ = f"Constant({value})"
	return Constant


BooleanExpressionAnd      = create_binary_operation(lambda l, r: l and r, "and")
BooleanExpressionOr       = create_binary_operation(lambda l, r: l or r, "or")
BooleanExpressionNot      = create_unary_operation(lambda x: not x, "not")
BooleanExpressionTrue     = create_constant(True)
BooleanExpressionFalse    = create_constant(False)

RelationalExpressionEq    = create_binary_operation(lambda l, r: l == r, "==")
RelationalExpressionNEq   = create_binary_operation(lambda l, r: l != r, "!=")
RelationalExpressionLT    = create_binary_operation(lambda l, r: l < r, "<")
RelationalExpressionGT    = create_binary_operation(lambda l, r: l > r, ">")
RelationalExpressionLE    = create_binary_operation(lambda l, r: l <= r, "<=")
RelationalExpressionGE    = create_binary_operation(lambda l, r: l >= r, ">=")

ArithmeticExpressionPlus  = create_binary_operation(lambda l, r: l + r, "+")
ArithmeticExpressionMinus = create_binary_operation(lambda l, r: l - r, "-")
ArithmeticExpressionMult  = create_binary_operation(lambda l, r: l * r, "*")
ArithmeticExpressionDiv   = create_binary_operation(lambda l, r: l / r, "/")
ArithmeticExpressionMod   = create_binary_operation(lambda l, r: l % r, "%")
ArithmeticExpressionNeg   = create_unary_operation(lambda x: -x, "-")
ArithmeticExpressionConst = create_constant()


if __name__ == "__main__":
	ctx = Context()
	block = []
	prog = StatementBlock(block)

	block.append(StatementWrite("Hello, World!\n"))
	block.append(StatementAssign(
		LocationValueVariable("foo"),
		ArithmeticExpressionPlus(
			ArithmeticExpressionConst(5),
			ArithmeticExpressionConst(7)
		)
	))
	block.append(StatementWriteInt(LocationValueVariable("foo")))
	block.append(StatementWrite("\n"))

	prog.execute(ctx)
