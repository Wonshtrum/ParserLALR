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


def member_getter(node):
	if isinstance(node, dict):
		return None, [(k, v) for k, v in node.items()]
	elif hasattr(node, "__iter__") and not isinstance(node, str):
		return None, [(k, v) for k, v in enumerate(node)]
	elif "__dict__" not in dir(node.__class__):
		return None, None
	else:
		return None, [(k, getattr(node, k)) for k in dir(node)
		if not callable(getattr(node, k))
		and not k.startswith("__")
		and k not in dir(node.__class__)]


def node_print(name, node, sub_getter, tab="", show_none=False):
	dec = " "
	result = f"{name}: " if name is not None else ""
	node_repr, sub_nodes = sub_getter(node)
	length = 0 if sub_nodes is None else len(sub_nodes)
	if length == 0:
		node_repr = repr(node) if node_repr is None else node_repr
		return f"{result}{node_repr}"
	node_repr = node.__class__.__name__ if node_repr is None else node_repr
	result = f"{result}{node_repr}"
	for i, (sub_node, value) in enumerate(sub_nodes):
		if value is None and not show_none:
			continue
		result += "\n"+tab
		if i == length-1:
			result += "└"
			pad = " "
		else:
			result += "├"
			pad = "│"
		result += node_print(sub_node, value, sub_getter, tab+pad+dec, show_none)
	return result
