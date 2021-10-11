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


def member_getter(obj):
	if "__dict__" not in dir(obj.__class__):
		return None
	return [_ for _ in dir(obj)
		if not callable(getattr(obj, _))
		and not _.startswith("__")]


def node_print(name, node, sub_getter, tab="", show_none=False):
	dec = " "
	result = str(name)
	if hasattr(node, "__iter__") and not isinstance(node, str):
		sub_nodes = range(len(node))
		#node = list(iter(node))
		get = lambda obj, attr: obj[attr]
		if len(node) == 0:
			sub_nodes = None
	else:
		get = lambda obj, attr: getattr(obj, attr)
		sub_nodes = sub_getter(node)
	if sub_nodes is None:
		return f"{name}: {repr(node)}"
	result = f"{name}: {node.__class__.__name__}"
	for i, sub_node in enumerate(sub_nodes):
		value = get(node, sub_node)
		if value is None and not show_none:
			continue
		result += "\n"+tab
		if i == len(sub_nodes)-1:
			result += "└"
			pad = " "
		else:
			result += "├"
			pad = "│"
		result += node_print(sub_node, value, sub_getter, tab+pad+dec, show_none)
	return result
