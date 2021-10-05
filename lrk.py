class NT:
	def __init__(self, name):
		self.name = name
	
	def __len__(self):
		return len(self.name)
	
	def __repr__(self):
		return self.name
	
	def __str__(self):
		return self.__repr__()


class Set(set):
	def update(self, elements):
		result = not self.issuperset(elements)
		super().update(elements)
		return result
	
	def add(self, element):
		result = element not in self
		super().add(element)
		return result


class Rules(dict):
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
			+("" if i else "\t\t -- {"+", ".join(str(_) for _ in self.follow)+"} {"+", ".join(str(_) for _ in self.first)+"}")
			for i, tokens in enumerate(self.tokens))

	def __str__(self):
		return self.__repr__()


def closure(f, verbose=lambda x:None):
	i = 0
	while f():
		i += 1
		verbose(i)


Start = NT("Start")
Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
rules = Rules()
rules.add_rules(
	(Start, [Add], ["$"]),
	(Add, [Add, "+", Factor]),
	(Add, [Factor]),
	(Factor, [Factor, "*", Term]),
	(Factor, [Term]),
	(Term, ["(", Add, ")"]),
	(Term, ["0"]),
	(Term, ["1"])
)
