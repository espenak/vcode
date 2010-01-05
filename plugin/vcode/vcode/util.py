import vim
from os.path import exists, join, splitext
import subprocess
from os import linesep

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

def colorDiff(title, lines):
	vim.command("tabnew " + title)
	vim.command("setlocal nonumber")
	vim.command("setlocal buftype=nofile")
	vim.command("setlocal bufhidden=delete")
	vim.command("setlocal noswapfile")
	vim.command("setlocal nobuflisted")
	vim.command("setlocal nowrap")
	syntax = (
		"syn match add #^+.*#",
		"syn match add #^+++.*#",
		"syn match remove #^-.*#",
		"syn match remove #^---.*#",
		"syn match info #^@@.*#",
		"syn match separator #^diff .*#",

		"hi def link add Statement",
		"hi def link remove Error",
		"hi def link info Special",
		"hi def link separator String",
	)
	for s in syntax:
		vim.command(s)
	vim.current.buffer[:] = lines
	vim.command("setlocal nomodifiable")

def colorDiffCommand(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout = p.communicate()[0]
	lines = stdout.split(linesep)
	print lines
	colorDiff("\\ ".join(cmd), lines)
