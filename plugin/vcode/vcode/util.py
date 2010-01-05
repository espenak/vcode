import vim
from os.path import exists, join, splitext

def goToWindowByNr(nr):
	vim.command('exec %d . "wincmd w"' % nr)

def windowNrFromName(name):
	return int(vim.eval("bufwinnr('^%s$')" % name))

def currentTabNr():
	return int(vim.eval("tabpagenr()"))

def goToWindowByBufName(name):
	orig = currentTabNr()
	while True:
		nr = windowNrFromName(name)
		if nr >= 0:
			goToWindowByNr(nr)
			return True
		vim.command("tabnext")
		if currentTabNr() == orig:
			return False

def cppAltHeaderFile():
	""" Opens the header file for the current c/c++ source file, if
	a .c/.cpp file is open, or the source file if a .h/.hpp file is
	open.
	
	You should have "set hidden" in your .vimrc to retain file history,
	and to enable switching files with unsaved changes.
	"""
	name = vim.current.buffer.name
	root, ext = splitext(name)
	if ext in (".h", ".hpp"):
		extensions = [".cpp", ".c"]
	elif ext in (".c", ".cpp"):
		extensions = [".hpp", ".h"]
	else:
		return

	for e in extensions:
		path = root + e
		if exists(path):
			vim.command("edit %s" % path)
			return
