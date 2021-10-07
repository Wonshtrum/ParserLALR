from lrk import NT, Rules, unroll, parse


Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
rules = Rules(
	(Add, [Add, "+", Factor]),
	(Add, [Factor]),
	(Factor, [Factor, "*", Term]),
	(Factor, [Term]),
	(Term, ["(", Add, ")"]),
	(Term, ["0"]),
	(Term, ["1"]),
)
rules, goto, states = unroll(rules, Add)
input()

E = NT("E")
B = NT("B")
rules = Rules(
	(E, [E, "*", B]),
	(E, [E, "+", B]),
	(E, [B, "-", E]),
	(E, [B]),
	(B, ["0"]),
	(B, ["1"]),
)
rules, goto, states = unroll(rules, E)
input()

E = NT("E")
B = NT("B")
rules = Rules(
	(E, [B, B]),
	(B, ["c", B]),
	(B, ["d"]),
)
rules, goto, states = unroll(rules, E)
input()
