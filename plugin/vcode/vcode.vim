python << EOF
import vim

p = vim.eval("globpath(&runtimepath, 'plugin/vcode')")
if p:
	import sys
	sys.path.append(p)
	from vcode.project import *
else:
	raise EnvironmentError("Could not find plugin/vimcode on runtime path.")

vCodeProj = VCodeProject("tull")
EOF



"map <C-M-Up> <ESC>:python altHeaderFile()<CR>
"map <F8> <ESC>:python vCodeProj.ui.view.open()<CR>
"au BufNewVCodeFile,BufRead *.h map <buffer> <C-M-Up> vCodeProj.()
