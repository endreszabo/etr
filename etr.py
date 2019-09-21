#!/usr/bin/python2
# -*- coding: utf-8 -*-

from config import *
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

engine = create_engine(db_connect_string, echo=True)
Session = sessionmaker(engine)
session = Session()
logopen()
pynotify.init("ETR")

def stop_tasks(reason=None):
	log(3,'Stopping running tasks')
	tasks = session.query(Task).filter(Task.started==True).all()
	if tasks:
		if len(tasks)>1:
			log(3,'ERROR, should be only one task running.', started_tasks=map(lambda task: task.id, tasks))
		for started_task in tasks:
			if started_task.started:
				log(3,'Stopped working on previously started task',task_id=started_task.id)
				started_task.started=False
				events = session.query(Event).filter(Event.task_id==started_task.id, Event.start!=None, Event.stop==None).all()
				if len(events)>1:
					log(3,'ERROR, should be only one event running.', started_tasks=map(lambda event: event.id, events))
				for event in events:
					event.stop=int(time())
					event.stop_reason=reason or 'Stopped task manually' 
				session.commit()
				return task
	else:
		log(3,'No task has been started at the moment.')
		return None

def get_partner(allow_new=True):
	partner = None
	while not partner:
		partners = session.query(Partner).all()
		partner_name=dmenu(map(lambda l_partner: l_partner.name, partners), prompt='Select partner:')
		partner = session.query(Partner).filter(Partner.name==partner_name).first()
		if partner:
			return partner
		elif allow_new:
			#new partner?
			log(3,'Getting partner short name')
			new_partner_shortname=dmenu([''.join(map(lambda item: item[0], partner_name.split(' ')))], prompt='No partner known with name of %s. Adding one. Enter their short name:' % partner_name)
			log(3,'Got partner short name', partner_shortname=new_partner_shortname)
			log(3,'Getting partner full name')
			new_partner_maildomains=dmenu([new_partner_shortname.lower()+'.hu'.lower()], prompt='Enter new partner email domains:')
			log(3,'Got partner full name', partner_name=partner_name)
			partner = Partner(shortname=new_partner_shortname, name=partner_name, maildomains=new_partner_maildomains.lower())
			log(3,'Adding new partner to database', shortname=new_partner_shortname, name=partner_name, maildomains=new_partner_maildomains.lower())
			session.add(partner)
			session.commit()
			partner_id=partner.id
			log(3,'Added partner', partner_id=partner.id)
		else:
			return None

def get_project(allow_new=True, partner=None):
	log(3,'Getting partner projects')
	project = None
	while not project:
		projects=session.query(Project).filter(Project.partner_id==partner.id).all()
		if projects:
			#if len(projects)==1:
			#	project=projects[0] #maybe later we can ask if user wants to add another project in this phase
			#	log(3,'Selected only project', project_name=project.name, project_id=project.id)
			#else:
				log(3,'More than one project can be found for partner, letting user select one')
				project_name=dmenu(map(lambda project: project.name, projects), prompt='Select or name a new project:')
				log(3,'User has selected project', project_name=project_name)
				log(3,'Looking up project id', project_name=project_name)
				project=session.query(Project).filter(Project.partner_id==partner.id, Project.name==project_name).first()
				if project:
					log(3,'Project found', project_name=project_name, project_id=project.id)
				else:
					log(3,'Project not found, creating new')
					project = Project(name=project_name, partner_id=partner.id)
					session.add(project)
					session.commit()
					log(3,'Created project', project_name=project.name, partner_id=partner.id, project_id=project.id)
		else:
			log(3,'No project could be found this partner, try to add one')
			new_project_name=dmenu([], prompt='No projects known for partner %s. Create one. Project name:' % partner.name)
			project = Project(name=new_project_name, partner_id=partner.id)
			log(3,'Adding new project to database', project_name=new_project_name, partner_id=partner.id)
			session.add(project)
			session.commit()
			project_id=project.id
			log(3,'Added project',project_id=project.id)
		return project

def get_contact(allow_new=True, partner=None):
	contact=None
	while not contact:
		contacts = session.query(Contact).filter(Contact.partner_id==partner.id).all()
		contact_name=dmenu(map(lambda l_contact: l_contact.name, contacts), prompt='Select contact at %s:' % partner.shortname)
		contact = session.query(Contact).filter(Contact.name==contact_name).first()
		if contact:
			return contact
		elif allow_new:
			shortname=None
			if ' ' in contact_name:
				shortname=''.join(map(lambda item: item[0], contact_name.split(' ')))
			else:
				shortname=contact_name
			new_contact_shortname=dmenu([shortname], prompt='Adding new contact. Enter shortname for %s:' % contact_name)
			new_contact_email=dmenu([
				contact_name.lower().replace(' ','.')+'@'+partner.maildomains,
				], prompt='Adding new contact. Enter email for %s:' % contact_name)
			contact = Contact(name=contact_name, shortname=new_contact_shortname, email=new_contact_email, partner_id=partner.id)
			log(3,'Adding new contact to database', contact_name=contact_name, contact_shortname=new_contact_shortname, email=new_contact_email, partner_id=partner.id)
			session.add(contact)
			session.commit()
			contact_id=contact.id
			log(3,'Added contact',contact_id=contact.id)
		else:
			return None

def get_task(partner=None, contact=None, project=None, new_task=False):
	task = None
	while not task:
		if new_task:
			log(3,'Asking user for new task name', partner_id=partner.id, contact_id=contact.id, project_id=project.id)
			names=session.query(func.count(Task.name),Task.name).group_by(Task.name).order_by(desc(func.count(Task.name))).all()
			new_task_name=dmenu(map(lambda task: task.name, names), prompt='New task name or choose from previously seen tasks:')
			task = Task(name=new_task_name, partner_id=partner.id, contact_id=contact.id, project_id=project.id, finished=False, started=False)
			session.add(task)
			session.commit()
			log(3,'Created task', task_name=task.name, task_started=task.started, task_finished=task.finished, task_id=task.id)
			return task
		else:
			tasks = session.query(Task).filter(
				Task.project_id==project.id,
				Task.contact_id==contact.id,
				Task.partner_id==partner.id
			).all()
			log(3,'Asking user for (new) task name', partner_id=partner.id, contact_id=contact.id, project_id=project.id)
			task_name=dmenu(map(lambda task: task.name, tasks), prompt='Task name or enter new name:')
			task = session.query(Task).filter(
				Task.project_id==project.id,
				Task.contact_id==contact.id,
				Task.partner_id==partner.id,
				Task.name==task_name
			).first()
			if not task:
				log(3,'Task not found', task_name=task_name, partner_id=partner.id, contact_id=contact.id, project_id=project.id)
				task = Task(name=task_name, partner_id=partner.id, contact_id=contact.id, project_id=project.id, finished=False, started=False)
				session.add(task)
				session.commit()
				log(3,'Created task', task_name=task.name, task_started=task.started, task_finished=task.finished, task_id=task.id)
				return task


def dmenu_yes_no(prompt='Yes/No?'):
	answer=dmenu(['Yes','No'],prompt=prompt)
	if answer=='Yes':
		return True
	return False

def is_task_running():
	tasks = session.query(Task).filter(Task.started==True).first()
	print tasks
	if tasks:
		return True
	return False

while True:
	selections=[]
	if is_task_running():
		selections.append('Stop task')
		selections.append('Finish task')
	selections.append('Start new task')
	selections.append('Switch task')
	selection=dmenu(selections, prompt='ETR Menu:')
	if not selection:
		sys.exit(0)
	if selection=='Stop task':
		reason=dmenu(['Lunch','Sleep'], prompt='Reason to stop task?')
		stop_tasks(reason)
	elif selection=='Start new task':
		partner = None
		contact = None
		project = None
		task = None
		while not partner:
			partner = get_partner(allow_new=True)
		while not contact:
			contact = get_contact(partner=partner)
		while not project:
			project = get_project(partner=partner)
		while not task:
			task = get_task(partner=partner, contact=contact, project=project, new_task=True)
		if dmenu_yes_no(prompt='Start task now?'):
			stop_tasks('Starting new task (ID: %s)' % task.id)
			task.started=True
			log(3,'Updated task', task_name=task.name, task_started=task.started, task_finished=task.finished, task_id=task.id)
			log(3,'Creating task event')
			event = Event(task_id=task.id, start=int(time()))
			session.add(event)
			session.commit()
			log(3,'Created task event', event_id=event.id, event_start=event.start)
			pynotify.Notification(partner.shortname, task.name+' created and started').show()
		else:
			pynotify.Notification(partner.shortname, task.name+' created').show()
	elif selection=='Switch task':
		unfinished_tasks=session.query(Task).filter(Task.finished==False, Task.started==False).all()
		selections=[]
		for task in unfinished_tasks:
			#i guess there are better ways to do this
			partner=session.query(Partner).filter(Partner.id==task.partner_id).first()
			project=session.query(Project).filter(Project.id==task.project_id).first()
			selections.append("%d: [%s] %s: %s" % (task.id, partner.shortname, project.name, task.name))
		task=dmenu(selections,prompt='Resume which task:')
		task=session.query(Task).filter(Task.id==task.split(':')[0]).first()
		stop_tasks('Switched task (ID: %d)' % task.id)
		task.started=True
		log(3,'Creating task event')
		event = Event(task_id=task.id, start=int(time()))
		session.add(event)
		session.commit()
		log(3,'Created task event', event_id=event.id, event_start=event.start)
		pynotify.Notification(partner.shortname, task.name+' resumed').show()
	elif selection=='Stop task':
		stop_tasks('Stopped manually')
		pynotify.Notification(partner.shortname, 'Started task stopped').show()
	elif selection=='Finish task':
		task=stop_tasks('Task finished')
		if task:
			log(3,'Setting stopped task as finished',task_id=task.id)
			task.finished=True
			session.commit()
		else:
			log(3,'ERROR: no running task was found')

