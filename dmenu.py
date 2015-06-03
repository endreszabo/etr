"""Python wrapper for dmenu

http://tools.suckless.org/dmenu/

"""
from subprocess import Popen, PIPE
from logger import log, loglevel
from time import sleep

class DMenuCancelled(Exception):
    pass

class Dmenu(object):
    bottom=False
    ignorecase=False
    lines=None
    monitor=None
    prompt=None
    font=None
    normal_background=None
    normal_foreground=None
    selected_background=None
    selected_foreground=None
    raise_on_exit=True
    def __init__(self, bottom=False, ignorecase=False, lines=None, monitor=None, prompt=None, font=None, normal_background=None, normal_foreground=None, selected_background=None, selected_foreground=None, raise_on_exit=False):
	self.bottom=bottom
	self.ignorecase=ignorecase
	self.lines=lines
	self.monitor=monitor
	self.prompt=prompt
	self.font=font
	self.normal_background=normal_background
	self.normal_foreground=normal_foreground
	self.selected_background=selected_background
	self.selected_foreground=selected_foreground
	self.raise_on_exit=raise_on_exit
	"""
	Open a dmenu to select an item
	:param items: A list of strings to choose from.
	:param bottom: dmenu appears at the bottom of the screen.
	:param ignorecase: dmenu matches menu items case insensitively.
	:param lines: dmenu lists items vertically, with the given number of lines.
	:param monitor: dmenu appears on the given Xinerama screen.
	:param prompt: defines the prompt to be displayed to the left of the input field.
	:param font: defines the font or font set used.
	:param normal_background: defines  the  normal background color.
	:param normal_foreground: defines the normal foreground color.
	:param selected_background: defines the selected background color.
	:param selected_foreground: defines the selected foreground color.
	For colors #RGB, #RRGGBB, and color names are supported.
	"""
    def build_commandline(self,
	bottom=False,
	ignorecase=False,
	lines=False,
	monitor=None,
	prompt=None,
	font=None,
	normal_background=None,
	normal_foreground=None,
	selected_background=None,
	selected_foreground=None):
	#I considered using a mapping {"bottom":"-b"} etc and passing **kwargs, but
	#that makes the function signature vague.
	args = ["dmenu"]
	if bottom or self.bottom:
	    args.append("-b")
	if ignorecase or self.ignorecase:
	    args.append("-i")
	if lines or self.lines:
	    args.extend(("-l", str(lines or self.lines)))
	if monitor or self.monitor:
	    args.extend(("-m", str(monitor or self.monitor)))
	if prompt or self.prompt:
	    args.extend(("-p", prompt or self.prompt))
	if font or self.font:
	    args.extend(("-fn", font or self.font))
	if normal_background or self.normal_background:
	    args.extend(("-nb", normal_background or self.normal_background))
	if normal_foreground or self.normal_foreground:
	    args.extend(("-nf", normal_foreground or self.normal_foreground))
	if selected_background or self.selected_background:
	    args.extend(("-sb", selected_background or self.selected_background))
	if selected_foreground or self.selected_foreground:
	    args.extend(("-sf", selected_foreground or selected_foreground))
	return args

    def dmenu(self, items, **kwargs):
	cli =self.build_commandline(**kwargs)
	input_str = "\n".join(items) + "\n"
	sleep(0.3) # avoiding xcompmgr bug.. yeah I know..
	proc = Popen(cli, stdout=PIPE, stdin=PIPE)
	retval = proc.communicate(input_str)[0]
	if self.raise_on_exit and not retval:
	    raise DMenuCancelled
	return retval.rstrip("\n")

if __name__ == '__main__':
	dmenu=Dmenu()
	dmenu=Dmenu(
	    font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
	    lines=10).dmenu
	print dmenu(['Yes','No'], prompt='Start task now?', lines=False)

