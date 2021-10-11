from sys import argv
from importlib.machinery import SourceFileLoader


def main(path, verbose=False):
	if not path.endswith("/"):
		path += "/"
	grammar = SourceFileLoader("grammar", path+"__init__.py").load_module()
	text = ""
	while True:
		entry = input("> ")
		if entry:
			text += entry
			continue
		lexer = grammar.GLexer(text)
		tokens, error = lexer.tokens()
		text = ""
		if error:
			print(error)
			continue
		if verbose:
			print(tokens)
		result, error = grammar.GParser.parse(tokens, lexer)
		if error:
			print(error)
			continue
		if verbose:
			print(result)
		if hasattr(result, "execute") and callable(result.execute):
			try:
				result.execute()
			except Exception as error:
				print(error)
		print("")


if __name__ == "__main__":
	if len(argv) > 1:
		if argv[1][0] == "-":
			if len(argv) > 2:
				verbose = "v" in argv[1]
				main(argv[2], verbose)
		else:
			main(argv[1])
