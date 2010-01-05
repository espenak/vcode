import sys
import vim
from fnmatch import fnmatch
from util import goToWindowByBufName




##############################################################
# File tree management
##############################################################

class FileTreeItem(object):
	def __init__(self, title, filename, depth):
		self.title = title
		self.filename = filename
		self.depth = depth
		self.meta = {} # a place for other parts of the system to attach metadata
		self.parent = None

	def listFormatPrefix(self, depth):
		return "".join(["| " for x in xrange(depth)])

	def getMeta(self, cls):
		""" Get the metadata entry for the given class. """
		if not cls.__name__ in self.meta:
			self.meta[cls.__name__] = {}
		return self.meta[cls.__name__]


class File(FileTreeItem):
	def __init__(self, title, filename, depth):
		super(File, self).__init__(title, filename, depth)

	def listFormat(self, depth):
		return self.listFormatPrefix(depth) + "|-" + self.title


class Group(FileTreeItem):
	def __init__(self, title, filename, depth, *items):
		super(Group, self).__init__(title, filename, depth)
		self.childLst = []
		self.childDct = {}
		for item in items:
			self.add(item)

	def getByIndex(self, index):
		return self.childLst[index]

	def getByTitle(self, title):
		return self.childDct[title]

	def add(self, item):
		self.childLst.append(item)
		self.childDct[item.title] = item
		item.parent = self

	def iterChildren(self):
		""" Iterate over the items directly below this folder. """
		for item in self.childLst:
			yield item

	def iterRecursive(self):
		""" Recurse the entire tree below this folder, including this folder. """
		yield self
		for item in self.childLst:
			if isinstance(item, Group):
				for i in item.iterRecursive():
					yield i
			else:
				yield item



##############################################################
# File index
##############################################################

class FileIndex(object):
	def __init__(self, root):
		self.root = root
		self._allItems = [x for x in self.root.iterRecursive()]

	def __iter__(self):
		return self._allItems.__iter__()

	def getByIndex(self, index):
		return self._allItems[index]

	def __getitem__(self, index):
		return self._allItems[index]





##############################################################
# Project browser
##############################################################


class ProjectBrowserFilter(object):
	def __init__(self, fnpatt=["*"]):
		self.fnpatt = fnpatt

	def letThrough(self, f):
		for patt in self.fnpatt:
			if fnmatch(f.filename, patt):
				return True
		return False


class ProjectBrowser(object):
	STDHEADER = [
			"\" ? for help",
			""]

	BUFNAME = "VCodeProjectExplorer"

	def __init__(self, index):
		self._fileindex = index
		self._filter = None
		self._setOpenFolder(self._fileindex.root, open=True)
		self._generateDisplay()
		self._curHeader = self.STDHEADER

	def _mapKeys(self):
		vim.command("noremap <buffer> <CR> <ESC>:python vCodeProj.ui.view.onSelect()<CR>")
		vim.command("noremap <buffer> <2-LeftMouse> <ESC>:python vCodeProj.ui.view.onSelect()<CR><ESC>")
		vim.command("noremap <buffer> <S-CR> <ESC>:python vCodeProj.ui.view.onSelect(alt=True)<CR>")

	def _redrawTree(self):
		self.open()
		cursor = vim.current.window.cursor
		b = vim.current.buffer
		vim.command("setlocal modifiable")
		b[:] = self._curHeader + self._toList()
		vim.command("setlocal nomodifiable")
		vim.current.window.cursor = cursor


	def _setupSyntaxHighlighting(self):
		syntax = (
			"syn match help #\" .*#",
			"syn match treePart #|[~+ -]#",
			"syn match treeFile #|-.*# contains=treePart",
			"syn match treeDir #|[+~].*# contains=treePart",
			"hi def link treePart Special",
			"hi def link treeDir Statement",
			"hi def link help Comment"
		)
		for s in syntax:
			vim.command(s)

	def _getItemUnderCursor(self):
		w = vim.current.window
		line, col = w.cursor
		index = line - len(self._curHeader) - 1
		return index, self._displayedItems[index]

	def _setOpenFolder(self, folder, open=True, recursive=False):
		""" Mark as open or closed folder. """
		if recursive:
			for i in folder.iterRecursive():
				if isinstance(i, Group):
					meta = i.getMeta(self.__class__)
					meta["open"] = open
		else:
			meta = folder.getMeta(self.__class__)
			meta["open"] = open

	def _openOrCloseFolder(self, folder, open=True, recursive=False):
		if not isinstance(folder, Group):
			return
		self._setOpenFolder(folder, open, recursive)
		self._generateDisplay()

	def _toList(self):
		l = []
		for item in self._displayedItems:
			prefix = "".join(["| " for x in xrange(item.depth)])
			if isinstance(item, Group):
				l.append("%s|~%s/" % (prefix, item.title))
			else:
				l.append("%s|-%s" % (prefix, item.title))
		return l

	def _isOpen(self, folder):
		meta = folder.getMeta(self.__class__)
		return meta.get("open", False)

	def _addThroughFilter(self, f):
		if self._filter != None and not self._filter.letThrough(f):
			return
		self._displayedItems.append(f)

	def _addToDisplay(self, folder):
		self._displayedItems.append(folder)
		if self._isOpen(folder):
			for item in folder.iterChildren():
				if isinstance(item, Group):
					self._addToDisplay(item)
				else:
					self._addThroughFilter(item)

	def _generateDisplay(self):
		self._displayedItems = []
		self._addToDisplay(self._fileindex.root)

	def _createBuffer(self):
		vim.command("tabnew %s" % self.BUFNAME)
		vim.command("setlocal nonumber")
		vim.command("setlocal buftype=nofile")
		vim.command("setlocal bufhidden=delete")
		vim.command("setlocal noswapfile")
		vim.command("setlocal nobuflisted")
		vim.command("setlocal visualbell") # disable beep on click
		vim.command("setlocal cursorline") # highlight current line
		vim.command("setlocal nowrap")
		self._setupSyntaxHighlighting()
		self._mapKeys()
		self._redrawTree()

	def applyFilter(self, filter):
		self._filter = filter
		self._generateDisplay()
		self._redrawTree()

	def clearFilter(self):
		self.applyFilter(None)

	def onSelect(self, alt=False):
		index, item = self._getItemUnderCursor()
		if index < 0:
			return
		if isinstance(item, Group):
			self._openOrCloseFolder(item, not self._isOpen(item), recursive=alt)
			self._redrawTree()
		else:
			vim.command("tabedit %s" % item.filename)
			vim.command("tabmove")
			if alt:
				self.moveCursorTo()

	def open(self):
		if not self.moveCursorTo():
			self._createBuffer()

	def moveCursorTo(self):
		return goToWindowByBufName(self.BUFNAME)





##############################################################
# User Interface
##############################################################

class UserInterface(object):
	def __init__(self, fileindex):
		self.items = fileindex
		self.view = ProjectBrowser(self.items)

	def show(self):
		self.view.open()
		self.view.applyFilter(ProjectBrowserFilter(["*.h", "*.c"]))



class Project(object):
	def __init__(self, path):
		self.fileindex = FileIndex(
			Group("Project root", None, 0,
				File("myfile.txt", "~/Desktop/tullball.txt", 1),
				File("stuff.c", "~/Desktop/stuff.c", 1),
				File("stuff.h", "~/Desktop/stuff.h", 1),
				Group("Subdir", None, 1,
					File("thestuff.c", "~/Desktop/stuff.c", 2),
					File("thestuff.h", "~/Desktop/stuff.h", 2),
					Group("SubSubdir", None, 2,
						File("thastuff.c", "~/Desktop/stuff.c", 3),
						File("thastuff.h", "~/Desktop/stuff.h", 3)
					)
				)
			)
		)
		self.ui = UserInterface(self.fileindex)
		self.ui.show()
