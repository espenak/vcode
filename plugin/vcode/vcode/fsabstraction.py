import re
from os import sep, getcwd, walk
from os.path import abspath, isdir, dirname


VIRTPATH_SEP = "/"
NORMALIZE_VPATH_PATT = re.compile(r"(?<=/)/|/+$")

def normVirtualPath(virtualPath):
	""" Just like os.path.normpath, but for virtual paths. """
	return NORMALIZE_VPATH_PATT.sub("", virtualPath)

def joinVirtualPath(a, b):
	""" Just like os.path.join, but for virtual paths. """
	return normVirtualPath(a + VIRTPATH_SEP + b)


class FsNode(object):
	def __init__(self, absPath, virtualPath):
		self._absPath = absPath
		self._virtPath = virtualPath
		self._parent = None

	def getAbsPath(self):
		return self._absPath

	def getVirtualPath(self):
		return self._virtPath

	def getParent(self):
		return self._parent


class FsFile(FsNode):
	pass


class FsDir(FsNode):
	def __init__(self, absPath, virtualPath):
		super(FsDir, self).__init__(absPath, virtualPath)
		self.childList = []

	def addChild(self, childNode):
		self.childList.append(childNode)


class FsIndex(object):

	def __init__(self, rootDir):
		self._rootDir = rootDir
		self._nodeLst = []
		self._nodeDct = {}

	def makeVirtualPath(self, absPath):
		""" Turn the absolute filesystem-path, *absPath*, into a virtual path
		relative to this FsIndex. """
		p = absPath.replace(self._rootDir, "").replace(sep, VIRTPATH_SEP)
		return p or "/"

	def absVirtualPath(self, relativeVirtualPath):
		""" Just like os.path.abspath, but for virtual paths is this FsIndex. """
		absPath = join(getcwd(), relativeVirtualPath)
		print absPath
		return self.makeVirtualPath(absPath)

	def _add(self, NodeCls, path):
		absPath = abspath(path)
		virtualPath = self.makeVirtualPath(absPath)
		if virtualPath in self._nodeDct:
			raise ValueError("%s is already in the FsIndex." % virtualPath)
		n = NodeCls(absPath, virtualPath)
		self._nodeLst.append(n)
		self._nodeDct[virtualPath] = n

		parentVirtPath = self.makeVirtualPath(dirname(absPath))
		parentDir = self._nodeDct.get(parentVirtPath)
		if parentVirtPath != virtualPath and parentDir != None:
			parentDir.addChild(n)

	def add(self, path):
		if isdir(path):
			self.addDir(path)
		else:
			self.addFile(path)

	def addDir(self, path):
		self._add(FsDir, path)

	def addDirRecursive(self, path):
		self.addDir(path)
		for root, dirs, files in walk(path):
			for d in dirs:
				self.addDir(join(root, d))
			for f in files:
				self.addFile(join(root, f))

	def addFile(self, path):
		self._add(FsFile, path)

	def getRootDir(self):
		return self._rootDir

	def getByVirtualPath(self, virtualPath):
		return self._nodeDct[virtualPath]




if __name__ == "__main__":
	import unittest
	from shutil import rmtree
	from tempfile import mkdtemp
	from os.path import join
	from os import chdir

	class TestFsIndex(unittest.TestCase):
		def setUp(self):
			self.tempDir = mkdtemp()
			chdir(self.tempDir)
			self.rootDir = getcwd() # should have been able to use self.tempDir, but it seems to fuck up the path..
			self.fileA = join(self.rootDir, "test.txt")
			open(self.fileA, "w").write("")
			self.i = FsIndex(self.rootDir)
	
		def tearDown(self):
			rmtree(self.tempDir)

		def testAdd(self):
			self.i.addDirRecursive(self.rootDir)
			a = self.i.getByVirtualPath("/test.txt")
			self.assertEquals(a.getVirtualPath(), "/test.txt")
			self.assertEquals(a.getAbsPath(), self.fileA)
			r = self.i.getByVirtualPath("/")
			self.assertEquals(r.getAbsPath(), self.rootDir)
			self.assertEquals(r.childList, [a])

		def testMakeVirtualPath(self):
			self.assertEquals(self.i.makeVirtualPath(self.fileA), "/test.txt")
			self.assertEquals(self.i.makeVirtualPath(self.rootDir), "/")

		def testMakeVirtualPath(self):
			self.assertEquals(self.i.absVirtualPath("test.txt"), "/test.txt")

	class TestModuleFunction(unittest.TestCase):
		def testNormVirtualPath(self):
			self.assertEquals(normVirtualPath("//hello/world///"),
					"/hello/world")

		def testJoinVirtualPath(self):
			self.assertEquals(joinVirtualPath("hello", "world"), "hello/world")
			self.assertEquals(joinVirtualPath("/hello//", "/world/"), "/hello/world")



	unittest.main()
