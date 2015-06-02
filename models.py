from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Partner(Base):
	__tablename__ = "partners"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	shortname = Column(String)
	maildomains = Column(String)

	def __repr__(self):
		return "<Partner(shortname='%s', name='%s', maildomains=%s)>" % (self.name, self.shortname, self.maildomains)

class Contact(Base):
	__tablename__ = "contacts"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	shortname = Column(String)
	email = Column(String)
	partner_id = Column(Integer, ForeignKey('partners.id'))

	def __repr__(self):
		return "<Contact(name='%s', email='%s', partner_id=%s)>" % (self.name, self.email, self.partner_id)

class Task(Base):
	__tablename__ = "tasks"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	started = Column(Boolean)
	finished = Column(Boolean)
	partner_id = Column(Integer, ForeignKey('partners.id'))
	project_id = Column(Integer, ForeignKey('projects.id'))
	contact_id = Column(Integer, ForeignKey('contacts.id'))

class Project(Base):
	__tablename__ = "projects"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	type = Column(Boolean)
	partner_id = Column(Integer, ForeignKey('partners.id'))

class Event(Base):
	__tablename__ = "events"
	id = Column(Integer, primary_key=True)
	task_id = Column(Integer, ForeignKey('tasks.id'))
	start = Column(Integer)
	stop = Column(Integer)
	stop_reason = Column(String)

class Object(Base):
	__tablename__ = "objects"
	id = Column(Integer, primary_key=True)
	event_id = Column(Integer, ForeignKey('events.id'))
	create_time = Column(Integer)
	name = Column(String)
	mime_type = Column(String)
	blob = LargeBinary()

