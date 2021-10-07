from utils import Set, MultiDict


class NT:
	def __init__(self, name):
		self.name = name

	def __len__(self):
		return len(self.name)

	def __repr__(self):
		return self.name

	def __str__(self):
		return self.__repr__()


class _EOF:
	def __repr__(self):
		return "$"

	def __str__(self):
		return self.__repr__()
EOF = _EOF()


class Rules(dict):
	def __init__(self, *rules):
		super().__init__()
		self.add_rules(*rules)

	def add_rule(self, product, tokens, follow=None):
		if product in self:
			self[product].tokens.append(tokens)
		else:
			self[product] = Rule(product, tokens, follow)

	def add_rules(self, *rules):
		for rule in rules:
			self.add_rule(*rule)

	def follow(self):
		dirty = False
		for rule in self.values():
			for tokens in rule.tokens:
				end = tokens[-1]
				if isinstance(end, NT):
					dirty = self[end].follow.update(rule.follow) or dirty
				for i, token in enumerate(tokens[1:]):
					nt = tokens[i]
					if isinstance(nt, NT):
						if isinstance(token, NT):
							dirty = self[nt].follow.update(self[token].first) or dirty
						else:
							dirty = self[nt].follow.add(token) or dirty
		return dirty

	def first(self):
		dirty = False
		for rule in self.values():
			for tokens in rule.tokens:
				first = tokens[0]
				if isinstance(first, NT):
					dirty = rule.first.update(self[first].first) or dirty
				else:
					dirty = rule.first.add(first) or dirty
		return dirty

	def __repr__(self):
		return "\n".join(str(rule) for rule in self.values())

	def __str__(self):
		return self.__repr__()


class Rule:
	def __init__(self, product, tokens=None, follow=None):
		self.product = product
		self.tokens = [] if tokens is None else [tokens]
		self.follow = Set() if follow is None else Set(follow)
		self.first = Set()
	
	def __getitem__(self, key):
		return (self.product, self.tokens[key], self.follow, self.first)

	def __repr__(self): 
		return f"{self.product} -> "+f"\n{' '*len(self.product)}  > ".join(
			" ".join(str(token)
			for token in tokens)
			+("" if i else "\t\t -- {"+", ".join(str(_)
			for _ in self.follow)+"} {"+", ".join(str(_)
			for _ in self.first)+"}")
			for i, tokens in enumerate(self.tokens))

	def __str__(self):
		return self.__repr__()


class State(dict):
	id = 0
	def get_id(self):
		State.id += 1
		return State.id

	def __init__(self, *positions):
		super().__init__()
		self.id = self.get_id()
		self.add_positions(*positions)

	def add_position(self, rule_id, product, tokens, position=0, look=None):
		key = (rule_id, position)
		if key in self:
			if look is not None:
				self[key].look.update(look)
		else:
			self[key] = Position(rule_id, product, tokens, position, look)

	def add_positions(self, *positions):
		for position in positions:
			self.add_position(*position)

	def add_rule(self, rule, look=None):
		for i, tokens in enumerate(rule.tokens):
			self.add_position((rule.product, i), rule.product, tokens, 0, look)

	def entail(self, rules):
		dirty = False
		new = []
		for position in self.values():
			if position.visited or position.on_end():
				continue
			position.visited = True
			dirty = True
			at = position.at()
			if isinstance(at, NT):
				rule = rules[at]
				if position.on_last():
					next = rule.follow
				elif isinstance(position.next(), NT):
					next = rules[position.next()].first
				else:
					next = [position.next()]
				new.append((rule, next))
		for rule, next in new:
			self.add_rule(rule, next)
		return dirty

	def tree(self):
		shift = {}
		reduce = {}
		for position in self.values():
			if position.on_end():
				for at in position.look:
					if at in reduce:
						print("reduce/reduce conflict:", at, "(", position, ")")
						print(self)
					else:
						reduce[at] = position.rule_id
			else:
				at = position.at()
				if at in shift:
					shift[at].add_position(*position.advance())
				else:
					shift[at] = State(position.advance())
		for at in reduce.keys():
			if at in shift:
				del shift[at]
				print("shift/reduce conflict:", at)
				print(self)
		return shift, reduce

	def __repr__(self):
		return f"State_{self.id}:\n"+"\n".join(str(position) for position in self.values())
	
	def __str__(self):
		return self.__repr__()


class Position:
	def __init__(self, rule_id, product, tokens, position=0, look=None):
		self.rule_id = rule_id
		self.product = product
		self.tokens = tokens
		self.position = position
		self.look = Set() if look is None else Set(look)
		self.visited = False

	def advance(self):
		return self.rule_id, self.product, self.tokens, self.position+1, self.look

	def at(self):
		return self.tokens[self.position]

	def next(self):
		return self.tokens[self.position+1]

	def on_last(self):
		return self.position+1 == len(self.tokens)

	def on_end(self):
		return self.position == len(self.tokens)
	
	def __eq__(self, other):
		return self.product == other.product and self.position == other.position and self.tokens == other.tokens and self.look == other.look

	def __repr__(self):
		return f"{self.product} {'=' if self.visited else '-'}> "+" ".join(("." if i == self.position else "")+str(token)
		for i, token in enumerate(self.tokens))+"\t\t -- {"+", ".join(str(token)
		for token in self.look)+"}"

	def __str__(self):
		return self.__repr__()


def closure(f, args=[], kwargs={}, verbose=lambda x:None):
	i = 0
	while f(*args, **kwargs):
		i += 1
		verbose(i)


def unroll(rules, START):
	ACCEPT = NT("__ACCEPT__")
	rules.add_rule(ACCEPT, [START, EOF])
	state = State()
	state.add_rule(rules[ACCEPT])
	
	closure(rules.first)
	closure(rules.follow)

	goto = {}
	merge = {}
	states = {}
	stack = [[state]]

	while stack:
		while stack[-1]:
			state = stack[-1].pop()
			closure(state.entail, args=(rules,))
			print("===============================================")
			print(state)
			for other in states.values():
				if state == other:
					print("merging", state.id, other.id)
					merge[state.id] = other.id
					break
			else:
				states[state.id] = state
				merge[state.id] = state.id

				shift, reduce = state.tree()
				stack.append(list(shift.values()))
				l = len(stack)
				for k, v in shift.items():
					key = (k, state.id)
					if key in goto:
						print("transition already in table")
					goto[key] = v.id
					print("\n"+"-"*l, k,":")
					print("-"*l, str(v).replace("\n","\n"+"-"*l+" "))
				for k, v in reduce.items():
					key = (k, state.id)
					if key in goto:
						print("transition already in table")
					goto[key] = v
				print("-----------------------------------------------")
				print(list(reduce.keys()))
		stack.pop()

	small_goto = {}
	small_states = {}
	small = {k:i for i, k in enumerate(states.keys())}
	for (token, state), v in goto.items():
		small_goto[(token, small[merge[state]])] = small[merge[v]] if isinstance(v, int) else v
	for k, v in states.items():
		small_states[small[k]] = v
		v.id = small[k]

	return rules, small_goto, small_states
