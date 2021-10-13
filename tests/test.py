from lalr.lrk import NT, Rules, unroll
from lalr.parser import Parser


E = NT("E")
B = NT("B")
rules = Rules(
	(E, [B, B]),
	(B, ["c", B]),
	(B, ["d"]),
)
rules, goto, states = unroll(rules, E, False)
Parser.ENTRIES = goto
Parser.print(1)
print("""0 : {E: 1, B: 2, 'c': 3, 'd': 4}
1 : {$: @}                      
2 : {B: 6, 'c': 7, 'd': 8}      
3 : {B: 5, 'c': 3, 'd': 4}      
4 : {'d': B, 'c': B}            
5 : {'d': B, 'c': B}            
6 : {$: E}                      
7 : {B: 9, 'c': 7, 'd': 8}      
8 : {$: B}                      
9 : {$: B}""")
print("------------------------------------")
input()
rules, goto, states = unroll(rules, E, True)
Parser.ENTRIES = goto
Parser.print(1)
print("""0 : {E: 1, B: 2, 'c': 4, 'd': 5}
1 : {$: @}                      
2 : {B: 3, 'c': 4, 'd': 5}      
3 : {$: E}                      
4 : {B: 6, 'c': 4, 'd': 5}      
5 : {'c': B, 'd': B, $: B}      
6 : {'c': B, 'd': B, $: B}""")
