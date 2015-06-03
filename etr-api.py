#!/usr/bin/python2
# -*- coding: utf-8 -*-

from dmenu import Dmenu
from re import findall
from time import time
from logger import *
import sys
import pynotify
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from models import *

dmenu=Dmenu(
    font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
    lines=10).dmenu

engine = create_engine('mysql://root@localhost/etr', echo=True)
Session = sessionmaker(engine)
session = Session()
logopen()
pynotify.init("ETR")

if sys.argv[1]=='get_current_event':
	log(3,'Getting running tasks')
	tasks = session.query(Task).filter(Task.started==True).all()
	if tasks:
		if len(tasks)>1:
			log(3,'ERROR, should be only one task running.', started_tasks=map(lambda task: task.id, tasks))
		for started_task in tasks:
			if started_task.started:
				log(3,'Stopped working on previously started task',task_id=started_task.id)
				events = session.query(Event).filter(Event.task_id==started_task.id, Event.start!=None, Event.stop==None).all()
				if len(events)>1:
					log(3,'ERROR, should be only one event running.', started_tasks=map(lambda event: event.id, events))
				print events[0].id
	else:
		log(3,'No task has been started at the moment')
		print "None"

