def pre_param(f, *args):
	def wrapper(*params):
		return f(*args, *params)
	return wrapper


class Pointer:
	def __init__(self, val):
		self.val = val


def shuffle(l, copy, make_tmp):
	goal = list(range(len(l)))
	tmp = None
	replace = lambda old, new: [new if _ == old else _ for _ in l]
	use_tmp = False
	change = True
	while change:
		change = False
		for dest in goal:
			src = l[dest]
			if src == dest:
				continue
			if dest in l:
				if not use_tmp:
					continue
				copy(tmp, dest)
				l = replace(dest, tmp)
			change = True
			copy(dest, src)
			l = replace(src, dest)
		if not change and not use_tmp:
			change = True
			use_tmp = True
			tmp = make_tmp()
