from sys import argv
from importlib.machinery import SourceFileLoader


def main(path):
	grammar = SourceFileLoader("shell", path).load_module()
	while True:
		text = input("> ")
		lexer = grammar.GLexer(text)
		tokens, error = lexer.tokens()
		if error:
			print(error)
			continue
		print(tokens)
		result, error = grammar.GParser.parse(tokens, lexer)
		if error:
			print(error)
			continue
		print(result)


if __name__ == "__main__":
	if len(argv) > 1:
		main(argv[1])
