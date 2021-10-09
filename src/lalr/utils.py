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
