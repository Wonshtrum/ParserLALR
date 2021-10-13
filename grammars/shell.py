from sys import argv
from importlib.machinery import SourceFileLoader


lexer = None
parser = None
result = None


def hasmethod(obj, method):
	return hasattr(obj, method) and callable(getattr(obj, method))


def compile(text, Lexer, parser, verbose=False):
	global lexer
	lexer = Lexer(text)
	tokens, error = lexer.tokens()
	if error:
		print(error)
		return
	result, error = parser.parse(tokens, lexer)
	if error:
		print(error)
		return
	if verbose:
		print(result)
	if hasmethod(result, "execute"):
		try:
			result.execute(*parser.get_execution_context())
		except Exception as error:
			print(error)
	return result


def main(path, files, verbose=False):
	global parser, result
	if not path.endswith("/"):
		path += "/"
	grammar = SourceFileLoader("grammar", path+"__init__.py").load_module()
	parser = grammar.GParser()
	for unit in files:
		text = open(unit, "r").read()
		print(text)
		parser = grammar.GParser()
		compile(text, grammar.GLexer, parser, verbose)
	text = ""
	while True:
		entry = input("> ")
		if entry:
			text += entry
			if entry == "CLEAR":
				parser = grammar.GParser()
				text = ""
			continue
		result = compile(text, grammar.GLexer, parser, verbose)
		parser = parser
		text = ""
		print("")


if __name__ == "__main__":
	if len(argv) > 1:
		if argv[1][0] == "-":
			if len(argv) > 2:
				verbose = "v" in argv[1]
				main(argv[2], argv[3:], verbose)
		else:
			main(argv[1], argv[2:])
