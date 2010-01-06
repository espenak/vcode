import sys
import vim
import fnmatch
from util import goToWindowByBufName




##############################################################
# File tree management
##############################################################

class FileTreeItem(object):
	def __init__(self, title, depth):
		self.title = title
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
		super(File, self).__init__(title, depth)
		self.filename = filename

	def listFormat(self, depth):
		return self.listFormatPrefix(depth) + "|-" + self.title


class Group(FileTreeItem):
	def __init__(self, title, depth, *items):
		super(Group, self).__init__(title, depth)
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
			if fnmatch.fnmatch(f.filename, patt):
				return True
		return False


class ProjectBrowser(object):
	STDHEADER = [
			"\" ? for help",
			""]

	BUFNAME = "VCodeProjectExplorer"

	def __init__(self, index):
		self._fileindex = index
		self._curFilter = None
		self._filters = {}
		self._setOpenGroup(self._fileindex.root, open=True)
		self._generateDisplay()
		self._curHeader = self.STDHEADER

	def _mapKey(self, key, action):
		vim.command("nmap <buffer> %s %s" % (key, action))

	def _mapKeys(self):
		o = "vCodeProj.browser"
		self._mapKey("<CR>", ":py %s.onSelect()<CR>" % o)
		self._mapKey("<2-LeftMouse>", ":py %s.onSelect()<CR>" % o)
		self._mapKey("<S-CR>", ":py %s.onSelect(alt=True)<CR>" % o)

		self._mapKey("<Right>", ":py %s.openGroup(recursive=False)<CR>" % o)
		self._mapKey("<S-Right>", ":py %s.openGroup(recursive=True)<CR>" % o)
		self._mapKey("<Left>", ":py %s.closeGroup(recursive=False)<CR>" % o)
		self._mapKey("<S-Left>", ":py %s.closeGroup(recursive=True)<CR>" % o)

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

	def _setOpenGroup(self, folder, open=True, recursive=False):
		""" Mark as open or closed folder. """
		if recursive:
			for i in folder.iterRecursive():
				if isinstance(i, Group):
					meta = i.getMeta(self.__class__)
					meta["open"] = open
		else:
			meta = folder.getMeta(self.__class__)
			meta["open"] = open

	def _openOrCloseGroup(self, folder, open=True, recursive=False):
		if not isinstance(folder, Group):
			return
		self._setOpenGroup(folder, open, recursive)
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
		if self._curFilter != None and not self._curFilter.letThrough(f):
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


	def autoCompleteFilternames(self):
		start = vim.eval("a:ArgLead")
		l = fnmatch.filter(self._filters.keys(), start + "*")
		vim.command("let result = %s" % repr(l))

	def addFilter(self, name, filter):
		self._filters[name] = filter

	def applyFilter(self, filterName):
		self._curFilter = self._filters.get(filterName)
		self._generateDisplay()
		self._redrawTree()

	def clearFilter(self):
		self.applyFilter(None)

	def onSelect(self, alt=False):
		index, item = self._getItemUnderCursor()
		if index < 0:
			return
		if isinstance(item, Group):
			self._openOrCloseGroup(item, not self._isOpen(item), recursive=alt)
			self._redrawTree()
		else:
			vim.command("tabedit %s" % item.filename)
			vim.command("tabmove")
			if alt:
				self.moveCursorTo()

	def _openOrCloseGroupUnderCursor(self, open=True, recursive=False):
		index, item = self._getItemUnderCursor()
		if index < 0:
			return
		if isinstance(item, Group):
			self._openOrCloseGroup(item, open, recursive)
			self._redrawTree()

	def openGroup(self, recursive=False):
		self._openOrCloseGroupUnderCursor(open=True, recursive=recursive)

	def closeGroup(self, recursive=False):
		self._openOrCloseGroupUnderCursor(open=False, recursive=recursive)


	def open(self):
		if not self.moveCursorTo():
			self._createBuffer()

	def moveCursorTo(self):
		return goToWindowByBufName(self.BUFNAME)





##############################################################
# User Interface
##############################################################

class Project(object):
	def __init__(self, path):
		self.fileindex = FileIndex(
			Group("Project root", 0,
				File("myfile.txt", "~/Desktop/tullball.txt", 1),
				File("stuff.c", "~/Desktop/stuff.c", 1),
				File("stuff.h", "~/Desktop/stuff.h", 1),
				Group("Subdir", 1,
					File("thestuff.c", "~/Desktop/stuff.c", 2),
					File("thestuff.h", "~/Desktop/stuff.h", 2),
					Group("SubSubdir", 2,
						File("thastuff.c", "~/Desktop/stuff.c", 3),
						File("thastuff.h", "~/Desktop/stuff.h", 3)
					)
				)
			)
		)

		self.browser = ProjectBrowser(self.fileindex)
		self.browser.addFilter("c/c++",
				ProjectBrowserFilter(["*.h", "*.c", "*.cpp", "*.hpp"]))
		self.browser.addFilter("txt",
				ProjectBrowserFilter(["*.txt"]))
		self.browser.open()
