"""
- Get:
	- Node by index-number (for the ui).
	- Node by path.
- Iter
	- Childnodes.
	- All nodes.
- Refresh:
	- Groups
	- Directories
- Reload all (config file changes).
- Each node has:
	- A view:
		- Short name.
		- Extra info added by plugins.
	- Parent node - except for the root node.
	- Event-handlers attached:
		- onRefresh()
		- onCreate()
		- onSelect()
		- onAltSelect()
		- onAtoZPressed()
- Each directory-node has:
	- Additional event-handlers:
		- onDelete()
		- onSave()
- Each file-node has:
	- Additional event-handlers:
		- onDelete()
		- onSave()
"""
from os.path import normpath, basename


class NodeView(object):
	""" A view is attached to every node in the datamodel.
	It is used by the UI to display the node.
	"""
	def __init__(self, name):
		self.name = name
		self.extraInfo = {}

	def iterExtraInfoSorted(self):
		""" Iterate over extraInfo.
		@return: (key,value) pairs ordered by key.
		"""
		keys = self.extraInfo.keys()
		keys.sort()
		for k in keys:
			yield k, self.extraInfo[k]

	def __unicode__(self):
		l = [self.name] + [v for k,v in self.iterExtraInfoSorted()]
		return u" ".join(l)


class Node(object):

	@classmethod
	def cmpNames(cls, a, b):
		return cmp(a.view.name, b.view.name)

	def __init__(self, name):
		self.parent = None
		self.view = NodeView(name)

	def refresh(self):
		pass


class ParentNode(Node):
	""" A node containing children. """

	def __init__(self, name):
		super(ParentNode, self).__init__(name)
		self._childList = []
		self._childDict = {}

	def addChild(self, node):
		node.parent = self
		if node.view.name in self._childDict:
			raise ValueError("Duplicate name: %s" % node.view.name)
		self._childList.append(node)
		self._childDict[node.view.name] = node

	def iterChildParentNodes(self):
		""" Iterate over all childnodes which is ParentNode instances. """
		for node in self._childList:
			if isinstance(node, ParentNode):
				yield node

	def iterChildren(self):
		return self._childList.__iter__()

	def getChildren(self):
		return self._childList

	def getChildByName(self, name):
		return self._childDict[name]

	def getChildByIndex(self, index):
		return self._childList[index]

	def sort(self):
		""" Sort this node, and all ParentNode's below it. """
		self._childList.sort(cmp=Node.cmpNames)
		for node in self.iterChildParentNodes():
			node.sort()

	def refresh(self):
		for node in self.iterChildParentNodes(self):
			node.refresh()


class Group(ParentNode):
	def __init__(self, name):
		super(Group, self).__init__(name)


class File(Node):
	def __init__(self, fileAbsPath):
		self.fileAbsPath = normpath(fileAbsPath)
		super(File, self).__init__(basename(self.fileAbsPath))


class Dir(Node):
	def __init__(self, fileAbsPath):
		self.fileAbsPath = normpath(fileAbsPath)
		super(Dir, self).__init__(basename(self.fileAbsPath))


if __name__ == "__main__":
	import unittest

	class TestView(unittest.TestCase):
		def testUnicode(self):
			v = NodeView("Hello")
			self.assertEquals(unicode(v), u"Hello")
			v.extraInfo["git"] = "[git:M]"
			v.extraInfo["vim"] = "*"
			self.assertEquals(unicode(v), u"Hello [git:M] *")

		def testIterExtraInfoOrdered(self):
			view = NodeView("Hello")
			view.extraInfo = dict(g="Two", a="One", z="Three")
			self.assertEquals(
					["One", "Two", "Three"],
					[v for k,v in view.iterExtraInfoSorted()])


	class TestParentNode(unittest.TestCase):
		def testSort(self):
			root = ParentNode("root")
			subroot = ParentNode("subroot")
			for name in ("b", "a", "z"):
				subroot.addChild(Node(name))
			root.addChild(subroot)
			root.addChild(Node("alfa"))
			root.sort()

			self.assertEqual(root.getChildByIndex(0).view.name, "alfa")
			self.assertEqual(root.getChildByIndex(1).view.name, "subroot")
			self.assertEqual(subroot.getChildByIndex(0).view.name, "a")

	unittest.main()
