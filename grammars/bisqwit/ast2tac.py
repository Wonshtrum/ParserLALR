from lalr.utils import Set, node_print, colored, uncolored, member_getter as default_getter
from .utils import Pointer, shuffle
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
		self.ident = ident
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
				return Statement(args[0], params=list(args[1:]))
		raise ValueError(f"Can't construct statement with {args}")

	def set(self, other):
		self.type = other.type
		self.ident = other.ident
		self.value = other.value
		self.params = other.params
		if other.type is not Statement.IFNZ:
			self.cond = Pointer(None)
		return self

	def copy(self):
		return Statement(self.type, self.ident, self.value, self.next.val, self.cond.val, list(self.params))

	def pure(self):
		if self.type is Statement.IFNZ:
			return False
		elif self.type is Statement.WRITE:
			return False
		elif self.type is Statement.FCALL:
			return False
		elif self.type is Statement.RET:
			return False
		return True

	def key(self):
		return (self.type, self.ident, self.value, self.next.val, self.cond.val, *self.params)

	def read_regs(self):
		if self.type is Statement.IFNZ or self.type is Statement.RET or self.type is Statement.WRITE:
			return zip(self.params, range(len(self.params)))
		return zip(self.params[1:], range(1, len(self.params)))

	def write_regs(self):
		if self.type is Statement.IFNZ or self.type is Statement.RET or self.type is Statement.WRITE:
			return []
		return zip(self.params[:1], [0])

	def __repr__(self):
		result = f"\t{self.type}\t"
		result += " ".join("..." if _ is None else f"R{_:02}" for _ in self.params)
		if self.type is Statement.INIT:
			ident = f'"{self.ident}"'
			result += f" {colored(ident,99)} {colored(self.value,201)}"
		return result

	def __str__(self):
		return self.__repr__()


for n in Statement.ENUM:
	locals()[f"s_{n}"]  = pre_param(Statement.constructor, n)
	locals()[f"is_s_{n}"] = pre_param(lambda n, s: isinstance(s, Statement) and s.type is n, n)
stmt = Statement.constructor


def follow(chain):
	while chain.val:
		yield chain.val
		chain = chain.val.next


class AccessInfo(dict):
	class Entry:
		def __init__(self, n_params, n_regs):
			self.params = [Set() for _ in range(n_params)]
			self.presence = [Set() for _ in range(n_regs)]

	def trace(self, where, state, follow_copies, include_ifnz_as_writers):
		n_changes = 0
		entry = self[where]
		max_regs_count = len(state)
		for r in range(max_regs_count):
			for source in state[r]:
				n_changes += entry.presence[r].add(source)
		if (follow_copies and is_s_copy(where)):
			if n_changes == 0:
				return
			state[where.params[0]] = Set(state[where.params[1]])
		else:
			for rr, ri in where.read_regs():
				for source in state[rr]:
					n_changes += entry.params[ri].add(source)
					if isinstance(source, Statement):
						for wr, wi in source.write_regs():
							if wr == rr:
								n_changes += self[source].params[wi].add(where)
			if n_changes == 0:
				return
			if include_ifnz_as_writers and is_s_ifnz(where):
				state[where.params[0]] = Set([where])
		for wr, wi in where.write_regs():
			if wr is not None:
				state[wr] = Set([where])
		if where.next.val is not None:
			state_ = state
			if where.cond.val is not None:
				state_ = [Set(_) for _ in state]
			self.trace(where.next.val, state_, follow_copies, include_ifnz_as_writers)
		if where.cond.val is not None:
			self.trace(where.cond.val, state, follow_copies, include_ifnz_as_writers)


	def run(self, env, follow_copies, include_ifnz_as_writers):
		max_regs_count = env.max_regs_count
		for s in env.statements:
			self[s] = AccessInfo.Entry(len(s.params), max_regs_count)
		for label, s in env.labels.items():
			state = [Set() for _ in range(max_regs_count)]
			num_params = env.num_params[label]
			for r in range(max_regs_count):
				if r < num_params:
					state[r].add((label, r))
				#else:
				#	state[r].add(None)
			self.trace(s.val, state, follow_copies, include_ifnz_as_writers)
		return self


OBSERVER = [None, True]
class Compilation:
	def __init__(self):
		self.string = ""
		self.statements = []
		self.num_params = {}
		self.labels = {}
		self.max_regs_count = 0

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
		result = None
		make = lambda: ctx.new_reg()
		put = lambda s: self.put(ctx, s)
		compile = lambda e: self.compile_expression(e, ctx)
		if is_deref(e):
			result = make()
			put(s_read(result, compile(e.params[0])))
		elif is_addrof(e):
			raise ValueError(f"Can't compile:\n {e}")
		elif is_neg(e):
			result = make()
			put(s_neg(result, compile(e.params[0])))
		elif is_ret(e):
			result = compile(e.params[0])
			put(s_ret(result))
		elif is_number(e):
			result = make()
			put(s_init(result, "", e.number))
		elif is_nop(e):
			put(s_nop())
		elif is_string(e):
			result = make()
			put(s_init(result, "$STR", self.string.index(e.string)))
		elif is_ident(e):
			ident = e.ident
			if is_function(ident):
				result = make()
				put(s_init(result, ident.name, 0))
			elif is_variable(ident):
				if ident.index in ctx.map:
					result = ctx.map[ident.index]
				else:
					result = ctx.map[ident.index] = make()
			elif is_parameter(ident):
				result = ident.index
		elif is_eq(e):
			left  = compile(e.params[0])
			right = compile(e.params[1])
			result = make()
			put(s_eq(result, left, right))
		elif is_add(e) or is_comma(e):
			result = left = compile(e.params[0])
			for param in e.params[1:]:
				right = compile(param)
				if is_add(e):
					result = make()
					put(s_add(result, left, right))
				else:
					result = right
				left = result
		elif is_copy(e):
			src, dest = e.params
			if is_deref(dest):
				result = compile(src)
				put(s_write(compile(dest.params[0]), result))
			else:
				tmp = compile(src)
				result = compile(dest)
				put(s_copy(result, tmp))
		elif is_fcall(e):
			result = make()
			put(s_fcall(result, *[compile(p) for p in e.params]))
		elif is_loop(e) or is_cand(e) or is_cor(e):
			is_and = not is_cor(e)
			result = make()
			b_then = s_init(result, "", 1 if is_and else 0)
			b_else = s_init(result, "", 0 if is_and else 1)
			b_end  = s_nop()
			if not is_loop(e):
				self.add(b_then)
			self.add(b_else, b_end)
			b_then.next.val = b_else.next.val = b_end
			begin = ctx.tgt
			for i, param in enumerate(e.params):
				var = compile(param)
				if is_loop(e) and i != 0:
					continue
				condition = ctx.tgt.val = s_ifnz(var, None)
				self.add(condition)
				if is_and:
					ctx.tgt = condition.cond
					condition.next.val = b_else
				else:
					ctx.tgt = condition.next
					condition.cond.val = b_else
			ctx.tgt.val = begin.val if is_loop(e) else b_then
			ctx.tgt = b_end.next
		return result

	def compile_function(self, f):
		self.num_params[f.name] = f.num_params
		self.labels[f.name] = Pointer(None)
		ctx = Context(f.num_params, self.labels[f.name])
		self.compile_expression(f.code, ctx)
		self.max_regs_count = max(self.max_regs_count, ctx.counter)

	def compile(self, context):
		self.build_strings(context)
		for f in context.func_list:
			self.compile_function(f)

	def generate_access_infos(self, follow_copies, include_ifnz_as_writers=False):
		return AccessInfo().run(self, follow_copies, include_ifnz_as_writers)

	def optimise_delete_nops(self):
		n_elisions = 0
		infos = self.generate_access_infos(False)
		equiv_nop = lambda s: (is_s_nop(s)
			or (is_s_ifnz(s) and (s.next.val is s.cond.val or s.cond.val is None))
			or (is_s_copy(s) and s.params[0] == s.params[1])
			or (s.pure() and not any(infos[s].params[wi] for wr, wi in s.write_regs()))
		)
		pending = list(self.labels.values())
		visited = Set()
		while pending:
			chain = pending.pop()
			while chain.val is not None and chain.val not in visited:
				if equiv_nop(chain.val) and chain.val is not chain.val.next.val:
					chain.val = chain.val.next.val
					n_elisions += 1
				visited.add(chain.val)
				if chain.val.cond.val is not None:
					pending.append(chain.val.cond)
				chain = chain.val.next
		for s, info in infos.items():
			if not s.pure():
				for wr, wi in s.write_regs():
					if not info.params[wi]:
						s.params[wi] = None
						n_elisions += 1
		print("elisions:", n_elisions)
		return n_elisions

	def optimise_GC(self):
		n_erased = 0
		changed = True
		while changed:
			changed = False
			pending = []
			visited = Set()
			for s in self.labels.values():
				pending.append(s.val)
			while pending:
				s = pending.pop()
				if not visited.add(s):
					continue
				if s.next.val:
					pending.append(s.next.val)
				if s.cond.val:
					pending.append(s.cond.val)
			for i in reversed(range(len(self.statements))):
				if self.statements[i] not in visited:
					self.statements.pop(i)
					n_erased += 1
					changed = True
		print("erased:", n_erased)
		return n_erased

	def optimise_jump_threading(self):
		n_threaded = 0
		for s in self.statements:
			if is_s_ret(s) and s.next.val is not None:
				s.next.val = None
				n_threaded += 1
			while is_s_ifnz(s) and is_s_ifnz(s.next.val) and s is not s.next.val and s.params[0] == s.next.val.params[0]:
				s.next.val = s.next.val.next.val
				n_threaded += 1
			while is_s_ifnz(s) and is_s_ifnz(s.cond.val) and s is not s.cond.val and s.params[0] == s.cond.val.params[0]:
				s.cond.val = s.cond.val.cond.val
				n_threaded += 1
			while is_s_init(s) and not s.ident and is_s_ifnz(s.next.val) and s.params[0] == s.next.val.params[0]:
				s.next.val = s.next.val.cond.val if s.value else s.next.val.next.val
				n_threaded += 1
			if is_s_copy(s) and is_s_ret(s.next.val) and s.next.val.params[0] in s.params:
				s.set(s_ret(s.params[1]))
				n_threaded += 1
		print("jumpthreaded:", n_threaded)
		return n_threaded

	def optimise_merge_trees(self):
		n_merged = 0
		hashes = {}
		for s in self.statements:
			key = s.key()
			if key in hashes:
				m_merged += 1
			hashes[s.key()] = s
		for s in self.statements:
			if s.next.val is not None:
				s.next.val = hashes[s.next.val.key()]
			if s.cond.val is not None:
				s.cond.val = hashes[s.cond.val.key()]
		print("merged:", n_merged)
		return n_merged

	def reach(self, start, end, exclude):
		pending = [start]
		visited = Set([exclude])
		while pending:
			chain = pending.pop()
			if not visited.add(chain):
				continue
			if chain is end:
				return True
			if chain.cond.val is not None:
				pending.append(chain.cond.val)
			if chain.next.val is not None:
				pending.append(chain.next.val)
		return False

	def get_literal(self, infos, sources, start, exact_value=True, with_ident=False):
		result = None
		for s in sources:
			value = None
			if s is not start:
				if is_s_init(s):
					if s.ident:
						if not with_ident:
							return None
						value = (s.ident, s.value)
					else:
						value = s.value if exact_value else bool(s.value)
						if with_ident:
							value = ("", value)
				elif is_s_ifnz(s):
					value = self.reach(s.cond.val, start, s)
					if value == self.reach(s.next.val, start, s):
						return None
					if value and exact_value:
						if not all(is_s_eq(source) for source in infos[s].params[0]):
							return None
					if with_ident:
						value = ("", value)
			if (result is not None and value != result) or value is None:
				return None
			result = value
		return result

	def optimise_simplify(self):
		n_folds = 0
		n_elisions = 0
		for include_ifnz_as_writers in (False, True):
			infos = self.generate_access_infos(True, include_ifnz_as_writers)
			for s, info in infos.items():
				get_literal = lambda sources, *args, **kwargs: self.get_literal(infos, sources, s, *args, **kwargs)
				if is_s_neg(s):
					op1 = get_literal(info.params[1])
					dest = s.params[0]
					if op1 is not None:
						s.set(s_init(dest, "", -op1))
						n_folds += 1
				elif is_s_add(s):
					op1 = get_literal(info.params[1])
					op2 = get_literal(info.params[2])
					dest = s.params[0]
					if op1 and op2:
						s.set(s_init(dest, "", op1+op2))
						n_folds += 1
					elif op1 == 0:
						s.set(s_copy(dest, s.params[2]))
						n_folds += 1
					elif op2 == 0:
						s.set(s_copy(dest, s.params[1]))
						n_folds += 1
				elif is_s_eq(s):
					dest = s.params[0]
					if info.params[1] == info.params[2]:
						s.set(s_init(dest, "", 1))
						n_folds += 1
						continue
					op1 = get_literal(info.params[1])
					op2 = get_literal(info.params[2])
					if op1 is not None and op2 is not None:
						s.set(s_init(dest, "", int(op1==op2)))
						n_folds += 1
				elif is_s_ifnz(s):
					op1 = get_literal(info.params[0], False)
					if op1 is not None:
						if op1:
							s.next.val = s.cond.val
						else:
							s.cond.val = s.next.val
						n_elisions += 1
						continue
					zero_reg = None
					for source in info.params[0]:
						if is_s_eq(source):
							info_source = infos[source]
							paramno = 0
							if get_literal(info_source.params[1]) == 0:
								paramno = 2
							elif get_literal(info_source.params[2]) == 0:
								paramno = 1
							else:
								break
							if zero_reg is None:
								zero_reg = source.params[paramno]
							elif zero_reg != source.params[paramno]:
								break
							if info.presence[zero_reg] != info_source.params[paramno]:
								break
						else:
							break
					else:
						if zero_reg is not None:
							s.params[0] = zero_reg
							s.cond.val, s.next.val = s.next.val, s.cond.val
							n_elisions += 1
				elif is_s_init(s):
					if n_elisions:
						continue
					dest = s.params[0]
					for r, sources in enumerate(info.presence):
						op1 = get_literal(sources, with_ident=True)
						if op1 == (s.ident, s.value):
							s.set(s_copy(dest, r))
							n_folds += 1
							break
				elif is_s_fcall(s):
					if not include_ifnz_as_writers and is_s_ret(s.next.val) and s.params[0] == s.next.val.params[0]:
						idents = set(_.ident if is_s_init(_) and _.value == 0 else None for _ in info.params[1])
						if len(idents) == 1 and list(idents)[0] in self.labels:
							jump = self.labels[list(idents)[0]].val
							params = s.params[2:]
							s.set(s_nop())
							p_tgt = Pointer(s.next)
							def copy(dest, src):
								p_tgt.val.val = s_copy(dest, src)
								self.statements.append(p_tgt.val.val)
								p_tgt.val = p_tgt.val.val.next
							def make_tmp():
								tmp = len(params)
								self.max_regs_count = max(self.max_regs_count, tmp)
								return tmp
							shuffle(params, copy, make_tmp)
							p_tgt.val.val = jump
		print("folds:", n_folds+n_elisions)
		return n_folds+n_elisions

	def optimise_copy_elision(self):
		def copy_readers(readers, wr):
			copies = []
			for reader in readers:
				if is_s_copy(reader) and reader.params[1] == wr and reader.params[0] != wr and (not copies or copies[0].params[0] == reader.params[0]):
					copies.append(reader)
				else:
					return []
			return copies

		infos = self.generate_access_infos(False)
		for s, info in infos.items():
			for wr, wi in s.write_regs():
				copies = copy_readers(info.params[wi], wr)
				if copies:
					valid_writes = {s: wi}
					nr = copies[0].params[0]
					if not (any(
						any(
							not isinstance(source, Statement) or (source not in valid_writes and any(
								wr2 == wr and (copy_readers(infos[source].params[wi2], wr2) != copies or (valid_writes.update({source: wi2}) and False)
								for wr2, wi2 in source.write_regs())))
							for source in infos[copy].params[1])
						for copy in copies)
						or any(
							any(
								infos[copy].presence[nr] != infos[write].presence[nr]
								for write in valid_writes)
							for copy in copies)
						):
						for ins, param_index in valid_writes.items():
							ins.params[param_index] = nr
						for copy in copies:
							copy.set(s_nop())
						print("copy_elisions:", 1)
						return True
			if is_s_copy(s) and s.params[0] != s.params[1]:
				dest = s.params[0]
				src = s.params[1]
				changes = 0
				for reader in info.params[0]:
					if isinstance(reader, Statement):
						dest_writers = infos[reader].presence[dest]
						if all(is_s_copy(writer) and writer.params == s.params and infos[writer].presence[src] == infos[s].presence[src] for writer in dest_writers):
							for rr, ri in s.read_regs():
								if rr == dest:
									reader.params[ri] = src
									changes = 0
				if changes:
					print("copy_elisions:", changes)
					return True
		print("copy_elisions:", 0)
		return False

	def optimise(self):
		OBSERVER[0] = self.statements
		while self.optimise_delete_nops() or self.optimise_GC() or self.optimise_jump_threading() or self.optimise_copy_elision() or self.optimise_simplify() or self.optimise_merge_trees():
			if str(self) != OBSERVER[0] and OBSERVER[1]:
				print(self)
				OBSERVER[0] = str(self)
				input()

	def __repr__(self, v=False):
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

		if v:
			for s in self.statements:
				if statistics[s].label is None:
					statistics[s].add_label()
			infos = self.generate_access_infos(False)

		result = f"{colored('STRINGS',3)}:\n{colored(self.string,99)}\n\n{colored('CODE',3)}:\n"
		while remaining:
			chain = remaining.pop(0)
			need_jmp = False
			for s in follow(chain):
				stats = statistics[s]
				if stats.done:
					if need_jmp:
						result += f"\tJMP\t{colored(stats.label,247)}\n"
					break
				stats.done = True
				line = ""
				if stats.label is not None:
					line += f"{colored(stats.label,247)}:"
				line += f"{s}"
				if s.cond.val is not None:
					branch_stats = statistics[s.cond.val]
					line += f" {colored(branch_stats.label,247)}"
					if not branch_stats.done:
						remaining.insert(0, s.cond)
				if v:
					line = line.expandtabs()
					length = len(uncolored(line))
					params = [[statistics[source].label if isinstance(source, Statement) else source for source in entry] for entry in infos[s].params]
					presence = {r:[statistics[source].label if isinstance(source, Statement) else source for source in entry] for r,entry in enumerate(infos[s].presence) if entry}
					line += f"{' '*(35-length)}{params}\n{' '*35}{presence}"
				result += f"{line}\n"
				need_jmp = True

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
