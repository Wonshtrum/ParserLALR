from lrk import NT, Rules, unroll


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
