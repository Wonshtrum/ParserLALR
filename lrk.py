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


class Set(set):
	def update(self, elements):
		result = not self.issuperset(elements)
		super().update(elements)
		return result

	def add(self, element):
		result = element not in self
		super().add(element)
		return result


class MultiDict(dict):
	def put(self, key, value):
		if key in self:
			self[key].append(value)
		else:
			self[key] = [value]


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
	def __init__(self, rules, *positions):
		super().__init__()
		self.rules = rules
		self.add_positions(*positions)

	def add_position(self, product, tokens, position=0, look=None):
		key = (product, *tokens, position)
		if key in self:
			if look is not None:
				self[key].look.update(look)
		else:
			self[key] = Position(product, tokens, position, look)

	def add_positions(self, *positions):
		for position in positions:
			self.add_position(*position)

	def add_rule(self, rule, look=None):
		for tokens in rule.tokens:
			self.add_position(rule.product, tokens, 0, look)
	
	def entail(self):
		dirty = False
		new = []
		for position in self.values():
			if position.visited or position.on_end():
				continue
			position.visited = True
			dirty = True
			at = position.at()
			if isinstance(at, NT):
				rule = self.rules[at]
				if position.on_last():
					next = rule.follow
				elif isinstance(position.next(), NT):
					next = self.rules[position.next()].first
				else:
					next = position.next()
				new.append((rule, next))
		for rule, next in new:
			self.add_rule(rule, next)
		return dirty
	
	def tree(self):
		shift = {}
		reduce = MultiDict()
		for position in self.values():
			if position.on_end():
				for at in position.look:
					reduce.put(at, position)
			else:
				at = position.at()
				if at in shift:
					shift[at].add_position(*position.advance())
				else:
					shift[at] = State(self.rules, position.advance())
		return shift, reduce

	def __repr__(self):
		return "\n".join(str(position) for position in self.values())
	
	def __str__(self):
		return self.__repr__()


class Position:
	def __init__(self, product, tokens, position=0, look=None):
		self.product = product
		self.tokens = tokens
		self.position = position
		self.look = Set() if look is None else Set(look)
		self.visited = False

	def advance(self):
		return self.product, self.tokens, self.position+1, self.look

	def at(self):
		return self.tokens[self.position]

	def next(self):
		return self.tokens[self.position+1]

	def on_last(self):
		return self.position+1 == len(self.tokens)
	
	def on_end(self):
		return self.position == len(self.tokens)

	def __repr__(self):
		return f"{self.product} {'=' if self.visited else '-'}> "+" ".join(("." if i == self.position else "")+str(token)
		for i, token in enumerate(self.tokens))+"\t\t -- {"+", ".join(str(token)
		for token in self.look)+"}"

	def __str__(self):
		return self.__repr__()


def closure(f, verbose=lambda x:None):
	i = 0
	while f():
		i += 1
		verbose(i)
	print("closure after", i)


Start = NT("Start")
Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
rules = Rules(
	(Start, [Add], [EOF]),
	(Add, [Add, "+", Factor]),
	(Add, [Factor]),
	(Factor, [Factor, "*", Term]),
	(Factor, [Term]),
	(Term, ["(", Add, ")"]),
	(Term, ["0"]),
	(Term, ["1"])
)
closure(rules.first)
closure(rules.follow)
print(rules)
state = State(
	rules,
	(Add, [Add, "+", Factor], 2, ["+", ")", EOF])
)
closure(state.entail)
print("--------------------")
print(state)
state = State(
	rules,
	(Term, ["(", Add, ")"], 1, ["*", "+", ")", EOF])
)
closure(state.entail)
print("--------------------")
print(state)
print("\n====================")


SS = NT("S'")
S = NT("S")
A = NT("A")
B = NT("B")
X = NT("X")
rules = Rules(
	(SS, [S, EOF]),
	(S, ["a", A, "b"]),
	(S, ["a", B, "d"]),
	(S, ["c", A, "d"]),
	(S, ["c", B, "b"]),
	(A, [X]),
	(B, [X]),
	(X, ["x"])
)
closure(rules.first)
closure(rules.follow)
print(rules)
state = State(
	rules,
	(S, ["a", A, "b"], 1, [EOF]),
	(S, ["a", B, "d"], 1, [EOF])
)
closure(state.entail)
print("--------------------")
print(state)
print("\n====================")
