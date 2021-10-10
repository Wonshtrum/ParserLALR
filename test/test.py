from lalr.lrk import NT, Rules, unroll
from lalr.parser import Parser


E = NT("E")
B = NT("B")
rules = Rules(
	(E, [B, B]),
	(B, ["c", B]),
	(B, ["d"]),
)
rules, goto, states = unroll(rules, E, True)
Parser.ENTRIES = goto
