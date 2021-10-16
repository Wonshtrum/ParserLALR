def pre_param(f, *args):
	def wrapper(*params):
		return f(*args, *params)
	return wrapper


class Pointer:
	def __init__(self, val):
		self.val = val
