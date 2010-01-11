"""
File memory model.

The virtual file-tree only cares about files. Directories are maintained as
Group-objects (with no path).
"""
from common import ENCODING


class FileTreeItem(object):
	def __init__(self, title, depth):
		"""
		@param title: The title displayed in the project browser.
		@param depth: The depth in the project browser (a integer).
		"""
		self.title = title.encode(ENCODING)
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
	""" A physical file. """
	def __init__(self, title, filepath, depth):
		"""
		@param filepath: The physical path to the file, relative to the
		location of the project.
		"""
		super(File, self).__init__(title, depth)
		self.filepath = filepath

	def listFormat(self, depth):
		return self.listFormatPrefix(depth) + "|-" + self.title


class Group(FileTreeItem):
	""" Container for files, and/or other Groups. """
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
		""" Iterate over the items directly below this group. """
		for item in self.childLst:
			yield item

	def iterRecursive(self):
		""" Recurse the entire tree below this folder, including this group. """
		yield self
		for item in self.childLst:
			if isinstance(item, Group):
				for i in item.iterRecursive():
					yield i
			else:
				yield item


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
