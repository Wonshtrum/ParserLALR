from sys import argv
from time import time
from importlib.machinery import SourceFileLoader


lexer = None
parser = None
result = None


def hasmethod(obj, method):
	return hasattr(obj, method) and callable(getattr(obj, method))


def compile(text, Lexer, parser, verbose=False, timed=False):
	global lexer
	t = time()
	lexer = Lexer(text)
	tokens, error = lexer.tokens()
	if timed:
		print("Lexer:", time()-t)
	if error:
		print(error)
		return
	t = time()
	result, error = parser.parse(tokens, lexer)
	if timed:
		print("Parser:", time()-t)
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


def main(path, files, verbose=False, immediate=False, timed=False):
	global parser, result, grammar
	if not path.endswith("/"):
		path += "/"
	grammar = SourceFileLoader("grammar", path+"__init__.py").load_module()
	parser = grammar.GParser()
	for unit in files:
		text = open(unit, "r").read()
		print(text)
		parser = grammar.GParser()
		result = compile(text, grammar.GLexer, parser, verbose, timed)
	if immediate:
		return grammar
	text = ""
	while True:
		entry = input("> ")
		if entry:
			text += entry
			if entry == "CLEAR":
				parser = grammar.GParser()
				text = ""
			elif entry == "QUIT":
				return grammar
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
				immediate = "i" in argv[1]
				timed = "t" in argv[1]
				grammar = main(argv[2], argv[3:], verbose, immediate, timed)
		else:
			grammar = main(argv[1], argv[2:])
		if grammar is not None:
			from grammar import *
