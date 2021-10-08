from my_lexers import LexerJSON
from my_parsers import ParserJSON
from time import time


json = open("data.json", "r").read()
lexer = LexerJSON(json)
tokens, error = lexer.tokens()
if error:
	print(error)
else:
	t = time()
	result = ParserJSON.parse(tokens)
	print(result)
	print(time()-t)
