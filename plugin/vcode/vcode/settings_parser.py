from os.path import isdir, join, dirname
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
	def __init__(self, filesNode, cwd, projectName):
		self._filesNode = filesNode
		self._cwd = cwd
		self._projectName = projectName

	def parse(self):
		head = Group("", -1)
		self._parseGroupNode(head, self._filesNode, self._projectName)
		return head.getByIndex(0)

	def _parseExclude(self, node, parentExclude=None):
		excludeNode = getChildNodeByNodeName(node, "exclude")
		if excludeNode:
			regex = PatternParser(excludeNode).toRegex()
			if not regex:
				return None
			inherit = excludeNode.getAttribute("inherit")
			if parentExclude and inherit:
				regex = "%s|%s" % (parentExclude, regex)
			return regex
		else:
			return None


	def _parseFileNode(self, parentGroup, node):
		parentGroup.add(File(
			node.getAttribute("title"),
			self._getAbsolutePath(node.getAttribute("path")),
			parentGroup.depth+1))

	def _parseDir(self, title, path, depth):
		g = Group(title, depth)
		for f in listdir(path):
			p = join(path, f)
			if isdir(p):
				g.add(self._parseDir(f, p, depth+1))
			else:
				g.add(File(f, p, depth+1))
		return g

	def _parseDirNode(self, parentGroup, node, excludePatt):
		excludePatt = self._parseExclude(node, excludePatt)
		path = self._getAbsolutePath(node.getAttribute("path"))
		group = self._parseDir(node.getAttribute("title"), path,
				parentGroup.depth+1)
		parentGroup.add(group)

	def _parseGroupNode(self, parentGroup, node, title=None, excludePatt=None):
		excludePatt = self._parseExclude(node, excludePatt)
		title = title or node.getAttribute("title")
		group = Group(title, parentGroup.depth+1)
		parentGroup.add(group)
		for c in node.childNodes:
			self._parseNode(group, c, excludePatt)

	def _parseNode(self, parentGroup, node, excludePatt=None):
		if node.nodeType != minidom.Node.ELEMENT_NODE:
			return
		elif node.tagName == "file":
			self._parseFileNode(parentGroup, node)
		elif node.tagName == "dir":
			self._parseDirNode(parentGroup, node, excludePatt)
		elif node.tagName == "group":
			self._parseGroupNode(parentGroup, node, excludePatt=excludePatt)

	def _getAbsolutePath(self, relativePath):
		return join(self._cwd, relativePath.replace(PATHNAME_SEP, sep))


class SettingsParser(object):
	def __init__(self, path):
		self.path = path
		self.cwd = dirname(path)
		self._dom = minidom.parse(path)
		self.projectName = self._dom.documentElement.getAttribute("name")

		filesNode = getChildNodeByNodeName(self._dom.documentElement, "files")
		self.files = FilesParser(filesNode, self.cwd, self.projectName).parse()
