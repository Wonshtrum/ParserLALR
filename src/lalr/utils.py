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


def enum_list(l, join=", ", final="or ", quote='"'):
	l = [f"{quote}{_}{quote}" for _ in l]
	if len(l) > 1:
		l[-1] = f"{final}{l[-1]}"
	return join.join(l)


class Node:
	def __init__(self, type, *args, **kwargs):
		self.type = type
		self.args = list(args)
		for k, v in kwargs.items():
			if hasattr(v, "__iter__"):
				self.add(Node(k, *v))
			else:
				self.add(Node(k, v))

	def add(self, arg):
		self.args.append(arg)
		return self

	def format(self, tab=""):
		dec = " "
		result = self.type
		for i, arg in enumerate(self.args):
			result += "\n"+tab
			if i == len(self.args)-1:
				result += "└"
				pad = " "
			else:
				result += "├"
				pad = "│"
			if isinstance(arg, Node):
				result += arg.format(tab+pad+dec)
			else:
				result += str(arg)
		return result

	def __repr__(self):
		return self.format()

	def __str__(self):
		return self.format()
