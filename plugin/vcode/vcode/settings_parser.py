from glob import glob
import re
from os.path import isdir, join, dirname, abspath, basename
from os import listdir, sep
import fnmatch
from xml.dom import minidom

from file_memorymodel import Group, File
from common import ENCODING


# Pathname separator used in settings files.
PATHNAME_SEP = "/"


def getChildNodeByNodeName(node, childName):
	""" Get the first childnode of "node" with nodeName "childName". """
	for child in node.childNodes:
		if child.nodeName == childName:
			return child
	return None

def getTextNodes(node):
	""" Merge all TEXT_NODE childnodes of "node" into a single string. """
	t = []
	for child in node.childNodes:
		if child.nodeType == minidom.Node.TEXT_NODE:
			t.append(child.nodeValue)
	return "".join(t)


class PatternCompiler(object):
	""" Turn lists of python regex and shell patterns into a
	single python regex.  """
	def __init__(self):
		self._pattern = []

	def addShellPatt(self, shellpatt):
		self._pattern.append(fnmatch.translate(shellpatt))

	def addRegex(self, regex):
		self._pattern.append(regex)

	def toRegex(self):
		p = "|".join(["(%s)" % x for x in self._pattern])
		return p


class PatternParser(object):
	""" Parse a XML node containing zero or one <shellpatterns> and zero or one
	<pyregex> node, each containing whitespace-separated patterns. """
	def __init__(self, patternNode):
		self._patternNode = patternNode
		self._patternCompiler = PatternCompiler()
		self._parseShellPatterns()
		self._parsePyRegex()

	def _parseList(self, nodename):
		n = getChildNodeByNodeName(self._patternNode, nodename)
		if not n:
			return []
		return getTextNodes(n).split()

	def _parseShellPatterns(self):
		for shellpatt in self._parseList("shellpatterns"):
			self._patternCompiler.addShellPatt(shellpatt)

	def _parsePyRegex(self):
		for regex in self._parseList("pyregex"):
			self._patternCompiler.addRegex(regex)

	def toRegex(self):
		return self._patternCompiler.toRegex()



class FilesParser(object):
	def __init__(self, rootDir, projectName):
		self._rootDir = rootDir
		self._projectName = projectName
		dom  = minidom.getDOMImplementation().createDocument(None, "allFiles",
				None)
		self._allFiles = dom.documentElement

	def addFiles(self, *filePaths):
		for path in filePaths:
			dom = minidom.parse(path)
			filesNode = dom.documentElement
			self._allFiles.appendChild(filesNode)

	def parse(self):
		rootGroup = Group(self._projectName, 0)
		self._parseFilesNode(rootGroup, self._allFiles.firstChild)
		return rootGroup

	def _parseFilesNode(self, rootGroup, filesNode):
		for node in filesNode.childNodes:
			self._parseNode(rootGroup, node, excludePatt=None)
		if filesNode != self._allFiles.lastChild:
			self._parseFilesNode(rootGroup, filesNode.nextSibling)

	def _parseExclude(self, node, parentExclude=None):
		excludeNode = getChildNodeByNodeName(node, "exclude")
		if excludeNode:
			inherit = excludeNode.getAttribute("inherit")
			regex = []
			if parentExclude and inherit == "yes":
				regex = [parentExclude]
			
			p = PatternParser(excludeNode).toRegex()
			if p:
				regex.append(p)
	
			if regex:
				return "|".join(regex)
			else:
				return None
		else:
			return parentExclude


	def _parseFileNode(self, parentGroup, node):
		path = node.getAttribute("path")
		parentGroup.add(File(
			node.getAttribute("title"),
			self.getRelativePath(path),
			self.getAbsolutePath(path),
			parentGroup.depth+1))

	def _parseDir(self, title, path, depth, compiledExcludePatt):
		g = Group(title, depth)
		for f in listdir(self.getAbsolutePath(path)):
			p = join(path, f)
			if isdir(self.getAbsolutePath(p)):
				g.add(self._parseDir(f, p, depth+1, compiledExcludePatt))
			else:
				if compiledExcludePatt and compiledExcludePatt.match(p):
					continue
				g.add(File(f, p, join(self._rootDir, p), depth+1))
		return g

	def _parseDirNode(self, parentGroup, node, excludePatt):
		excludePatt = self._parseExclude(node, excludePatt)
		if excludePatt:
			compiledExcludePatt = re.compile(excludePatt)
		else:
			compiledExcludePatt = None
		path = node.getAttribute("path")
		title = node.getAttribute("title")
		group = self._parseDir(title, path,
				parentGroup.depth+1, compiledExcludePatt)
		parentGroup.add(group)

	def _parseGroupNode(self, parentGroup, node, excludePatt=None):
		excludePatt = self._parseExclude(node, excludePatt)
		title = node.getAttribute("title")
		group = Group(title, parentGroup.depth+1)
		for c in node.childNodes:
			self._parseNode(group, c, excludePatt)
		parentGroup.add(group)

	def _parseNode(self, parentGroup, node, excludePatt=None):
		if node.nodeType != minidom.Node.ELEMENT_NODE:
			return
		elif node.tagName == "file":
			self._parseFileNode(parentGroup, node)
		elif node.tagName == "dir":
			self._parseDirNode(parentGroup, node, excludePatt)
		elif node.tagName == "group":
			self._parseGroupNode(parentGroup, node, excludePatt=excludePatt)

	def getRelativePath(self, relativePath):
		return relativePath.replace(PATHNAME_SEP, sep)

	def getAbsolutePath(self, relativePath):
		return join(self._rootDir, self.getRelativePath(relativePath))


class SettingsParser(object):
	def __init__(self, projectDir):
		self.projectDir = abspath(projectDir)
		self.rootDir = dirname(self.projectDir)
		self.projectName = basename(projectDir).replace(".vcode", "")

		f = FilesParser(self.rootDir, self.projectName)
		filePaths = glob(join(self.projectDir, "*.files.xml"))
		filePaths.sort()
		f.addFiles(*filePaths)
		self.files = f.parse()
