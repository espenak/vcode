python << EOF
import vim

p = vim.eval("globpath(&runtimepath, 'plugin/vcode')")
if p:
	import sys
	sys.path.append(p)
	from vcode.project import *
	import vcode.util
else:
	raise EnvironmentError("Could not find plugin/vimcode on runtime path.")

vCodeProj = VCodeProject("tull")
EOF




function VCodeReccomendedKeymaps()
	au BufNewFile,BufRead *.h map <buffer> <C-M-Up> :python vcode.util.cppAltHeaderFile()<CR>
	au BufNewFile,BufRead *.c map <buffer> <C-M-Up> :python vcode.util.cppAltHeaderFile()<CR>
	au BufNewFile,BufRead *.cpp map <buffer> <C-M-Up> :python vcode.util.cppAltHeaderFile()<CR>
	au BufNewFile,BufRead *.hpp map <buffer> <C-M-Up> :python vcode.util.cppAltHeaderFile()<CR>
	"map <F8> <ESC>:python vCodeProj.ui.view.open()<CR>
endfunction


function VCodeReccomendedSettings()
	" Hide buffer instead of deleting it when the buffer closes.
	" This makes buffers retain undo-history. Especially important
	" if you use altHeaderFile.
	set hidden
endfunction

call VCodeReccomendedSettings()
call VCodeReccomendedKeymaps()
