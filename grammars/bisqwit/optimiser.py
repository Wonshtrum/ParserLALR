from .ast import *


class Pointer:
	def __init__(self, val):
		self.val = val


def for_all_expr(f, tree, *args):
	for param in tree.params:
		if for_all_expr(f, param, *args):
			return True
	return f(tree, *args)


def is_pure_fcall(e, context):
	if not is_fcall(e):
		return False
	f = e.params[0]
	if not is_ident(f) or not is_function(f.ident):
		return False
	f = context.func_list[f.ident.index]
	return f.pure_known and f.pure


def has_side_effect(e, caller, unknown_functions, context):
	if is_copy(e):
		return for_all_expr(is_deref, e.params[1])
	if is_fcall(e):
		f = e.params[0]
		if not is_ident(f) or not is_function(f.ident):
			return True
		f = context.func_list[f.ident.index]
		if f.pure_known and not f.pure:
			return True
		if not f.pure_known and f is not caller:
			print(f"{caller} calls unknown function {f.name}")
			unknown_functions.val = True
		return False
	return False


def check_purity(context):
	func_list = context.func_list
	for f in func_list:
		f.pure = False
		f.pure_known = False
	dirty = True
	while dirty:
		dirty = False
		for f in func_list:
			if f.pure_known:
				continue
			unknown_functions = Pointer(False)
			side_effects = for_all_expr(has_side_effect, f.code, f, unknown_functions, context)
			if (side_effects or not unknown_functions.val):
				f.pure_known = True
				f.pure = not side_effects
				print(f"{f.name} purity: {f.pure}")
				dirty = True


def adopt(e, is_child, get_children):
	i = 0
	while i < len(e.params):
		sub = e.params[i]
		if is_child(sub, i):
			e.params = e.params[:i]+get_children(sub, i)+e.params[i+1:]
		else:
			i += 1


s=lambda e:(for_all_expr(simplify, e, None) and False) or print(e)
def simplify(e, context):
	if is_add(e) or is_comma(e) or is_cor(e) or is_cand(e):
		adopt(e,
			lambda sub, i: sub.type is e.type,
			lambda sub, i: sub.params)
	if is_add(e):
		acc = sum(_.number for _ in e.params if is_number(_))
		e.params = [_ for _ in e.params if not is_number(_)]
		adopt(e,
			lambda sub, i: is_neg(sub) and is_add(sub.params[0]),
			lambda sub, i: [e_neg(_) for _ in sub.params[0].params])
		if acc != 0:
			e.add(acc)
		if sum(is_neg(_) for _ in e.params) > len(e.params)//2:
			e.set(e_neg(e_add(e_neg(_) for _ in e.params)))
	elif is_neg(e):
		sub = e.params[0]
		if is_number(sub):
			e.set(-sub.number)
		elif is_neg(sub):
			e.set(sub.params[0])
		elif is_add(sub) and len(sub.params) > 1 and is_number(sub.params[-1]):
			if sum(is_neg(_) for _ in sub.params) >= len(sub.params)//2:
				e.set(e_add(e_neg(_) for _ in sub.params))
	elif is_eq(e):
		a, b = e.params
		if is_number(a) and is_number(b):
			e.set(int(a==b))
		elif a == b and a.is_pure():
			e.set(1)
	elif is_deref(e):
		if is_addrof(e.params[0]):
			e.set(e.params[0].params[0])
	elif is_addrof(e):
		if is_deref(e.params[0]):
			e.set(e.params[0].params[0])
	elif is_cand(e) or is_cor(e):
		value_kind = is_true if is_cand(e) else is_false
		params = []
		early_cut = False
		for param in e.params:
			if is_number(param):
				if not value_kind(param):
					early_cut = True
					break
			else:
				params.append(param)
		e.params = params
		if early_cut:
			e.params = [_ for _ in e.params if not _.is_pure()]
			e.set(e_comma(e.copy(), 0 if is_cand(e) else 1))
	elif is_copy(e):
		a, b = e.params
		if a == b and a.is_pure():
			e.set(a)
	elif is_loop(e):
		if is_false(e.params[0]):
			e.set(e_nop())
		else:
			params = e.params
			i = 1
			while i < len(params):
				param = params[i]
				if param.is_pure():
					params.pop(i)
				else:
					if is_add(param) or is_neg(param) or is_eq(param) or is_addrof(param) or is_deref(param) or is_comma(param):
						params = params[:i]+param.params+params[i+1:]
					elif is_pure_fcall(param, context):
						params = params[:i]+param.params[1:]+params[i+1:]
					else:
						if is_ret(param) or (is_loop(param) and is_true(param.params[0])):
							params = params[:i+1]
					i += 1
			e.params = params
	elif is_comma(e):
		i = 0
		params = e.params
		while i < len(params):
			param = params[i]
			if i == len(params)-1:
				i += 1
			elif param.is_pure():
				params.pop(i)
			else:
				if is_add(param) or is_neg(param) or is_eq(param) or is_addrof(param) or is_deref(param) or is_comma(param):
					params = params[:i]+param.params+params[i+1:]
				elif is_pure_fcall(param, context):
					params = params[:i]+param.params[1:]+params[i+1:]
				else:
					if is_ret(param) or (is_loop(param) and is_true(param.params[0])):
						params = params[:i+1]
				i += 1
		e.params = params

	length = len(e.params)
	if length == 0:
		if is_add(e) or is_cor(e):
			e.set(0)
		elif is_cand(e):
			e.set(1)
	elif length == 1:
		if is_add(e) or is_comma(e):
			e.set(e.params[0])
		elif is_cor(e) or is_cand(e):
			e.set(e_eq(e_eq(e, 0), 0))


def optimise(context):
	check_purity(context)
	for f in context.func_list:
		for_all_expr(simplify, f.code, context)
