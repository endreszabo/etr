#!/usr/bin/python2
# -*- coding: utf-8 -*-

from config import *
from email import Parser
from email.Utils import parseaddr
from dmenu import Dmenu
from re import findall
from time import time
from logger import *

import email
import subprocess
import sys
import pynotify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *

dmenu=Dmenu(
    font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
    lines=10).dmenu

engine = create_engine(db_connect_string, echo=True)
Session = sessionmaker(engine)
session = Session()
logopen()
pynotify.init("ETR Started Task")

def decode_header_ng(h):
	"""
	Recodes header into utf-8
	"""
	items=decode_header(h)
	parts=[]
	for item in items:
		if item[1] == None:
			parts.append(item[0])
		else:
			parts.append(item[0].decode(item[1]).encode('utf-8'))
	return ' '.join(parts)

for partner in session.query(Partner).all():
	log(3,'partner',partner=partner)

log(3,'begin mail processing from stdin')
mail_parser=Parser.Parser()
parsed_mail=mail_parser.parsestr(sys.stdin.read())
log(3,'mail parsed')

from email.header import decode_header
log(3,'parsing mail From: header')
mail_from=parseaddr(parsed_mail.get('From'))
mail_from_decoded=decode_header_ng(mail_from[0])
mail_domain=mail_from[1].split('@')[1]
log(3,'mail From: header parsed', raw_name=mail_from[0], decoded_name=mail_from_decoded, mail_address=mail_from[1], mail_domain=mail_domain)
if mail_from_decoded=='':
	log(3,'Looks like From: header has no name, crafting one from email address')
	mail_from_decoded=' '.join(findall(r"\w+", mail_from[1].split('@')[0]))
	if mail_from_decoded:
		log(3,'Crafted a name', original_from=mail_from[1], to=mail_from_decoded)
	else:
		log(3,'Failed, continuing anyway')

log(3,'Checking for known contact with this address', mail_address=mail_from[1])

contact = session.query(Contact).filter(Contact.email==mail_from[1]).first()
partner = None
project = None
event = None

contact_id=None

if contact:
	log(3,'Contact found', contact_name=contact.name, contact_id=contact.id)
	contact_id=contact.id
	partner=session.query(Partner).filter(Partner.id==contact.partner_id).first()
	log(3,'Contact found at known partner', contact_id=contact.id, partner_id=partner.id, contact_name=contact.name, partner_name=partner.name)
else:
	log(3,'Contact not found, try to create one.')
	mail_domain_lower=mail_domain.lower()
	log(3,'Checking parters with this email domain', mail_domain=mail_domain_lower)
	partners = session.query(Partner).all()
	log(3,'Processing partners',num_partners=len(partners))
	partner_id=None
	for cur_partner in partners:
		if mail_domain_lower in cur_partner.maildomains.split(','):
			partner = cur_partner
			log(3,'Found partner with maildomain', name=partner.name, partner_id=partner.id, maildomains=partner.maildomains)
			partner_id = partner.id
			break
	if not partner_id:
		log(3,'No partner could be found this this maildomain, try to add one')
		log(3,'Getting partner short name')
		new_partner_shortname=dmenu([mail_domain, '<Append to existing partner>'], prompt='No partner is known with mail domain of %s. Adding one. Enter their short name:' % mail_domain,
			font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
			lines=10)
		new_partner_shortname=new_partner_shortname.strip()
		if new_partner_shortname=='<Append to existing partner>':
			partners = session.query(Partner).all()
			existing_partner_name=dmenu(
				map(lambda l_partner: l_partner.name, partners),
				prompt='Select partner to append to.',
				font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
				lines=10)
			existing_partner_name=existing_partner_name.strip()
			partner=session.query(Partner).filter(Partner.name==existing_partner_name).first()
			if not partner:
				log(3, "Selected existing partner not found, bailing out", existing_partner_name=existing_partner_name)
				sys.exit(3)
			partner.maildomains+=','+mail_domain
			partner_id = partner.id
			session.commit()
		else:
			log(3,'Got partner short name', partner_shortname=new_partner_shortname)
			log(3,'Getting partner full name')
			new_partner_name=dmenu([mail_domain], prompt='Enter new partner full name:',
				font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
				lines=10)
			new_partner_name=new_partner_name.strip()
			log(3,'Got partner full name', partner_name=new_partner_name)
			partner = Partner(shortname=new_partner_shortname, name=new_partner_name, maildomains=[mail_domain_lower])
			log(3,'Adding new partner to database', shortname=new_partner_shortname, name=new_partner_name, maildomains=[mail_domain_lower])
			session.add(partner)
			session.commit()
			partner_id=partner.id
			log(3,'Added partner', partner_id=partner.id)
	names=[mail_from_decoded]
	name_backwards=mail_from_decoded.split(' ')
	if len(name_backwards)>1:
		name_backwards.reverse()
		names.append(' '.join(name_backwards))
	new_contact_name=dmenu(names, prompt='%s contact not known, adding one. Name:' % partner.shortname,
		font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
		lines=10)
	new_contact_name=new_contact_name.strip()
	if ' ' in new_contact_name:
		shortname=''.join(map(lambda item: item[0], new_contact_name.split(' ')))
	else:
		shortname=new_contact_name
	new_contact_shortname=dmenu([shortname], prompt='Enter shortname for %s:' % new_contact_name,
		font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
		lines=10)
	new_contact_shortname=new_contact_shortname.strip()
	contact = Contact(name=new_contact_name, shortname=new_contact_shortname, email=mail_from[1], partner_id=partner.id)
	log(3,'Adding new contact to database', contact_name=new_contact_name, contact_shortname=new_contact_shortname, email=mail_from[1], partner_id=partner.id)
	session.add(contact)
	session.commit()
	contact_id=contact.id
	log(3,'Added contact',contact_id=contact.id)


log(3,'Decoding mail subject',raw_subject=parsed_mail.get('Subject'))
subject=decode_header_ng(parsed_mail.get('Subject'))
log(3,'Decoded mail subject',raw_subject=parsed_mail.get('Subject'), subject=subject)

log(3,'Getting partner projects')
projects=session.query(Project).filter(Project.partner_id==partner.id).all()
if projects:
	#if len(projects)==1:
	#	project=projects[0] #maybe later we can ask if user wants to add another project in this phase
	#	log(3,'Selected only project', project_name=project.name, project_id=project.id)
	#else:
		log(3,'More than one project can be found for partner, letting user select one')
		project_name=dmenu(map(lambda project: project.name, projects), prompt='Select a project:',
			font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
			lines=10)
		project_name=project_name.strip()
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
	new_project_name=dmenu([subject], prompt='No projects known for partner %s. Create one. Project name:' % partner.name,
		font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
		lines=10)
	new_project_name=new_project_name.strip()
	project = Project(name=new_project_name, partner_id=partner.id)
	log(3,'Adding new project to database', project_name=new_project_name, partner_id=partner.id)
	session.add(project)
	session.commit()
	project_id=project.id
	log(3,'Added project',project_id=project.id)

log(3,'Asking user for new task name', partner_id=partner.id, contact_id=contact.id, project_id=project.id)
new_task_name=dmenu([subject], prompt='Task name:',
	font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true',
	lines=10)
new_task_name=new_task_name.strip()
task = Task(name=new_task_name, partner_id=partner.id, contact_id=contact.id, project_id=project.id, finished=False, started=False)
session.add(task)
session.commit()
log(3,'Created task', task_name=task.name, task_started=task.started, task_finished=task.finished, task_id=task.id)

start=dmenu(['Yes','No'], prompt='Start task now?',
	font='Inconsolata for Powerline:pixelsize=16:antialias=true:hinting=true')
start=start.strip()
if start == 'Yes':
	log(3,'User selected to work on this task. Stopping other running tasks')
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
					event.stop_reason='Switched to other task (ID: %d)' % (task.id)
				session.commit()
	else:
		log(3,'No task has been started at the moment, $USER is what a lazy person!')
	task.started=True
	log(3,'Updated task', task_name=task.name, task_started=task.started, task_finished=task.finished, task_id=task.id)
	log(3,'Creating task event')
	event = Event(task_id=task.id, start=int(time()))
	session.add(event)
	session.commit()
	log(3,'Created task event', event_id=event.id, event_start=event.start)
else:
	log(3,'User selected not to work on this task. Creating a container event anyway')
	event = Event(task_id=task.id, start=int(time()), stop=int(time()), stop_reason='Automatic payload insertion')
	session.add(event)
	session.commit()
	log(3,'Event created without active task', event_id = event.id)
log(3,'Inserting original e-mail into task event', event_id = event.id)
blob_object = Object(
	event_id=event.id,
	create_time=int(time()),
	name='Original e-mail message',
	mime_type='message/rfc822',
	blob=parsed_mail.as_string()
	)
session.add(blob_object)
session.commit()
log(3,'Inserted blob object', object_id=blob_object.id)

pynotify.Notification(partner.shortname, task.name).show()
