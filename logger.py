from inspect import stack
from time import time
loglevel=3
import syslog
startupid=0

def logopen():
	startupid=int(time())
	syslog.openlog(ident='etr', logoption=syslog.LOG_PID + syslog.LOG_CONS)
	syslog.syslog(slog('stream.info: Starting up', verbose_level='3', version='1.0', startup_id=int(time())))

def logclose():
	syslog.closelog()

def logd(level=loglevel, message=None, kwargs={}):
	if level>=loglevel:
		str="%s(%d): %s" % (stack()[1][3],startupid,'; '.join([message,', '.join(map(lambda (k,v): "%s='%s'" % (k,v), kwargs.iteritems()))]))
		print(str)
		syslog.syslog(str)

def log(level=loglevel, message=None, **kwargs):
	if level>=loglevel:
		str="%s(%d): %s" % (stack()[1][3],startupid,'; '.join([message,', '.join(map(lambda (k,v): "%s='%s'" % (k,v), kwargs.iteritems()))]))
		print(str)
		syslog.syslog(str)

def slog(message=None, **kwargs):
	return "%s" % ('; '.join([message,', '.join(map(lambda (k,v): "%s='%s'" % (k,v), kwargs.iteritems()))]))
