from lrk import NT, EOF, Rules, State, closure


Start = NT("Start")
Add = NT("Add")
Factor = NT("Factor")
Term = NT("Term")
rules = Rules(
	(Start, [Add], [EOF]),
	(Add, [Add, "+", Factor]),
	(Add, [Factor]),
	(Factor, [Factor, "*", Term]),
	(Factor, [Term]),
	(Term, ["(", Add, ")"]),
	(Term, ["0"]),
	(Term, ["1"]),
)
closure(rules.first)
closure(rules.follow)
print(rules)
state = State(
	(Add, [Add, "+", Factor], 2, ["+", ")", EOF]),
)
closure(state.entail, args=(rules,))
print("--------------------")
print(state)
state = State(
	(Term, ["(", Add, ")"], 1, ["*", "+", ")", EOF]),
)
closure(state.entail, args=(rules,))
print("--------------------")
print(state)
print("\n====================")


SS = NT("S'")
S = NT("S")
A = NT("A")
B = NT("B")
X = NT("X")
rules = Rules(
	(SS, [S, EOF]),
	(S, ["a", A, "b"]),
	(S, ["a", B, "d"]),
	(S, ["c", A, "d"]),
	(S, ["c", B, "b"]),
	(A, [X]),
	(B, [X]),
	(X, ["x"]),
)
closure(rules.first)
closure(rules.follow)
print(rules)
state = State(
	(SS, [S, EOF]),
	#(S, ["a", A, "b"], 1, [EOF]),
	#(S, ["a", B, "d"], 1, [EOF]),
)
closure(state.entail, args=(rules,))
print("--------------------")
print(state)
print("\n====================")


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
