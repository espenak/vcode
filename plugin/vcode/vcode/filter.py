

class Pattern(object):
	MATCH = 1
	CONTINUE = 2
	ABORT = 3

	def check(self, path):
		raise NotImplementedError()


class ShellPattern(Pattern):
	def __init__(self, pattern):
		self._negative = shellPatt[0] == "-"
		self._pattern = shellPatt[1:]

	def check(self, path):
		match = fnmatch.fnmatchcase(path, self._pattern)
		if not match:
			return Pattern.CONTINUE
		elif self._negative:
			return Pattern.ABORT
		else:
			return Pattern.MATCH


class Filter(object):
	def __init__(self, patterns=[]):
		self._patterns = patterns

	def addPattern(self, pattern):
		self._patterns.append(pattern)

	def filter(self, filePaths):
		def f(path):
			for patt in self._patterns:
				r = patt.check(path)
				if r == Pattern.MATCH:
					return True
				elif r == Pattern.ABORT:
					return False
			return False
