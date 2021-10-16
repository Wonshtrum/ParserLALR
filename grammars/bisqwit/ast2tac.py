from lalr.utils import node_print, colored, member_getter as default_getter
from .utils import Pointer
from .ast import *


class Statement:
	NOP = "nop"
	INIT = "init"
	ADD = "add"
	NEG = "neg"
	COPY = "copy"
	READ = "read"
	WRITE = "write"
	EQ = "eq"
	IFNZ = "ifnz"
	FCALL = "fcall"
	RET = "ret"
	ENUM = [NOP, INIT, ADD, NEG, COPY, READ, WRITE, EQ, IFNZ, FCALL, RET]

	def __init__(self, type, ident=None, value=None, next=None, cond=None, params=None):
		self.type = type
		self.ident = None if ident is None else f'"{ident}"'
		self.value = value
		self.next = Pointer(next)
		self.cond = Pointer(cond)
		self.params = [] if params is None else params

	def constructor(*args):
		if not args:
			return Statement(Statement.NOP)
		elif len(args) == 1:
			if any(args[0] is _ for _ in Statement.ENUM):
				return Statement(args[0])
			elif isinstance(args[0], Statement):
				return args[0]
		elif any(args[0] is _ for _ in Statement.ENUM):
			if args[0] is Statement.INIT:
				return Statement(Statement.INIT, args[2], args[3], params=[args[1]])
			elif args[0] is Statement.IFNZ:
				return Statement(Statement.IFNZ, cond=args[2], params=[args[1]])
			else:
				return Statement(args[0], params=args[1:])
		raise ValueError(f"Can't construct statement with {args}")

	def __repr__(self):
		result = f"\t{self.type}\t"
		result += " ".join(f"R{_:02}" for _ in self.params)
		if self.type is Statement.INIT:
			result += f" {colored(self.ident,99)} {colored(self.value,201)}"
		return result

	def __str__(self):
		return self.__repr__()


for n in Statement.ENUM:
	locals()[f"s_{n}"]  = pre_param(Statement.constructor, n)
	locals()[f"is_s_{n}"] = pre_param(lambda n, e: e.type is n, n)
stmt = Statement.constructor


class Compilation:
	def __init__(self):
		self.string = ""
		self.statements = []
		self.num_params = {}
		self.labels = {}

	def build_strings(self, context):
		strings = []
		for f in context.func_list:
			for_all_expr(lambda e: is_string(e) and strings.append(e.string) and False, f.code)
		strings.sort(key=len, reverse=True)
		for string in strings:
			if string not in self.string:
				self.string += string

	def add(self, *statements):
		for s in statements:
			self.statements.append(s)

	def put(self, ctx, s):
		self.statements.append(s)
		ctx.tgt.val = s
		s = Pointer(s)
		while s.val is not None:
			s = s.val.next
			ctx.tgt = s

	def compile_expression(self, e, ctx):
		result = 0
		make = lambda: ctx.new_reg()
		put = lambda s: self.put(ctx, s)
		compile = self.compile_expression
		if is_deref(e):
			result = make()
			put(s_read(result, compile(e.params[0], ctx)))
		elif is_addrof(e):
			raise ValueError(f"Can't compile:\n {e}")
		elif is_neg(e):
			result = make()
			put(s_neg(result, compile(e.params[0], ctx)))
		elif is_ret(e):
			result = compile(e.params[0], ctx)
			put(s_ret(result))
		elif is_number(e):
			result = make()
			put(s_init(result, "", e.number))
		elif is_nop(e):
			result = make()
			put(s_init(result, "", 0))
		elif is_string(e):
			result = make()
			put(s_init(result, "$STR", self.string.index(e.string)))
		elif is_ident(e):
			ident = e.ident
			if is_function(ident):
				result = make()
				put(s_init(result, ident.name, 0))
			elif is_variable(ident):
				result = ctx.map[ident.index] = make()
			elif is_parameter(ident):
				result = ident.index
		elif is_add(e) or is_eq(e) or is_comma(e):
			left = compile(e.params[0], ctx)
			for param in e.params[1:]:
				right = compile(param, ctx)
				if is_add(e):
					result = make()
					put(s_add(result, left, right))
				elif is_eq(e):
					result = make()
					put(s_eq(result, left, right))
				else:
					result = right
				left = result
		elif is_copy(e):
			src, dest = e.params
			if is_deref(dest):
				result = compile(src, ctx)
				put(s_write(compile(dest.params[0], ctx), result))
			else:
				tmp = compile(src, ctx)
				result = compile(dest, ctx)
				put(s_copy(result, tmp))
				result = tmp
		elif is_fcall(e):
			result = make()
			put(s_fcall(result, *[compile(p, ctx) for p in e.params]))
		elif is_loop(e) or is_cand(e) or is_cor(e):
			is_and = not is_cor(e)
			result = make()
			b_then = s_init(result, "", 1 if is_and else 0)
			b_else = s_init(result, "", 0 if is_and else 1)
			b_end  = s_nop()
			self.add(b_then, b_else, b_end)
			b_then.next.val = b_else.next.val = b_end
			begin = ctx.tgt.val
			for i, param in enumerate(e.params):
				var = compile(param, ctx)
				if is_loop(e) and i < len(e.params)-1:
					continue
				condition = ctx.tgt.val = s_ifnz(var, None)
				self.add(condition)
				if is_and:
					ctx.tgt = condition.cond
					condition.next.val = b_else
				else:
					ctx.tgt = condition.next
					condition.cond.val = b_else
			ctx.tgt.val = begin if is_loop(e) else b_then
			ctx.tgt = b_end.next
		return result

	def compile_function(self, f):
		self.num_params[f.name] = f.num_params
		self.labels[f.name] = Pointer(None)
		ctx = Context(f.num_params, self.labels[f.name])
		self.compile_expression(f.code, ctx)

	def compile(self, context):
		self.build_strings(context)
		for f in context.func_list:
			self.compile_function(f)

	def __repr__(self):
		class Stats:
			LABELS = 0
			def __init__(self):
				self.label = None
				self.done = False
				self.referred = False

			def add_label(self):
				Stats.LABELS += 1
				self.label = f"L{Stats.LABELS-1}"

		statistics = {}
		for s in self.statements:
			statistics[s] = Stats()

		for s in self.statements:
			if s.next.val is not None:
				t = statistics[s.next.val]
				if t.label is None:
					if t.referred:
						t.add_label()
					t.referred = True
			if s.cond.val is not None:
				t = statistics[s.cond.val]
				if t.label is None:
					t.add_label()

		remaining = []
		for label, s in self.labels.items():
			remaining.append(s)
			statistics[s.val].label = label

		result = f"{colored('STRINGS',3)}:\n{colored(self.string,99)}\n\n{colored('CODE',3)}:\n"
		while remaining:
			chain = remaining.pop(0)
			need_jmp = False
			while chain.val is not None:
				stats = statistics[chain.val]
				if stats.done:
					if need_jmp:
						result += f"\tJMP\t{colored(stats.label,247)}\n"
					break
				stats.done = True
				if stats.label is not None:
					result += f"{colored(stats.label,247)}:"
				result += f"{chain.val}"
				if chain.val.cond.val is not None:
					branch_stats = statistics[chain.val.cond.val]
					result += f" {colored(branch_stats.label,247)}"
					if not branch_stats.done:
						remaining.insert(0, chain.val.cond)
				result += "\n"
				need_jmp = True
				chain = chain.val.next

		return result


class Context:
	def __init__(self, start, tgt):
		self.counter = start
		self.tgt = tgt
		self.map = {}

	def new_reg(self):
		self.counter += 1
		return self.counter-1


def compile(context):
	env = Compilation()
	env.compile(context)
	print(env)
	return env
