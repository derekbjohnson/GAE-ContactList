'''Reference GAE documentation / Guestbook example
http://stackoverflow.com/questions/11874934/overwrite-in-datastore-using-python-for-gae-guestbook-example
http://stackoverflow.com/questions/17621515/how-to-show-and-hide-input-fields-based-on-radio-button-selection
http://stackoverflow.com/questions/17646667/dynamic-dropdown-list-in-python-gae
'''

import cgi
import webapp2
import urllib
import os
import jinja2

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api.datastore_types import Key

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

DEFAULT_CONTACTLIST_NAME = 'default_contactlist'

#parent key ensures all contacts are in the same entity group
#queries across the entity group will be consistent.

def contactlist_key(contactlist_name=DEFAULT_CONTACTLIST_NAME):
	"""Constructs a datastore key for a contactlist entity with contactlist_name"""
	#return db.Key('Guestbook', guestbook_name)
	return db.Key.from_path('Contactlist', contactlist_name or 'default_contactlist')

class Contact(db.Model):
	"""Models an individual Contactlist entry"""
	firstname = db.StringProperty()#required=True)
	lastname = db.StringProperty()#required=True)
	email = db.EmailProperty()
	address = db.StringProperty()
	city = db.StringProperty()
	state = db.StringProperty()
	phone = db.PhoneNumberProperty()
	avatar = db.BlobProperty(default=None)

class Image(webapp2.RequestHandler):
	def get(self):
		contact = db.get(self.request.get('img_id'))
		if contact.avatar:
			self.response.headers['Content-Type'] = 'image/png'
			self.response.out.write(contact.avatar)
		else:
			self.response.out.write('No image')

class MainPage(webapp2.RequestHandler):
	def get(self):
		contactlist_name = self.request.get('contactlist_name',
			DEFAULT_CONTACTLIST_NAME)

		optionsbox = db.GqlQuery("SELECT state FROM Contact")
		optionsbox = set(optionsbox)
		
		contacts = db.GqlQuery('SELECT * '
								'FROM Contact '
								'WHERE ANCESTOR IS :1 '
								'ORDER BY lastname DESC ',
								contactlist_key(contactlist_name))

		showlink = False
		url = ""
		url_linktext = ""

		template_values = {
			'optionsbox': optionsbox,
			'contacts': contacts,
			'contactlist_name': urllib.quote_plus(contactlist_name),
			'url': url,
			'url_linktext': url_linktext,
			'showlink': showlink,
		}

		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))

class Filter(webapp2.RequestHandler):
	def post(self):
		contactlist_name = self.request.get('contactlist_name',
			DEFAULT_CONTACTLIST_NAME)

		optionsbox = self.request.get('statefilter')
		
		contacts = db.GqlQuery('SELECT * '
								'FROM Contact '
								'WHERE ANCESTOR IS :1 '
								'AND state = :2 '
								'ORDER BY lastname DESC ',
								contactlist_key(contactlist_name), optionsbox)

		url = '/?' + urllib.urlencode({'contactlist_name': contactlist_name})
		url_linktext = 'Main Page'
		showlink = True

		template_values = {
			'optionsbox': optionsbox,
			'contacts': contacts,
			'contactlist_name': urllib.quote_plus(contactlist_name),
			'url': url,
			'url_linktext': url_linktext,
			'showlink': showlink,
		}

		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))

class ContactList(webapp2.RequestHandler):
	def post(self):
		#set the same parent key on the 'Contact' to ensure each Contact is in the 
		#same entity group; queries across the group will be consistent
		contactlist_name = self.request.get('contactlist_name')
		
		if (not self.request.get('key') and self.request.get('img')):
			contact = Contact(parent=contactlist_key(contactlist_name))
			contact.firstname = self.request.get('firstname')
			contact.lastname = self.request.get('lastname')
			contact.email = self.request.get('email')
			contact.address = self.request.get('address')
			contact.city = self.request.get('city')
			contact.state = self.request.get('state')
			contact.phone = self.request.get('phone')
			avatar = images.resize(self.request.get('img'), 32, 32)
			contact.avatar = db.Blob(avatar)
			contact.put()
		else:
			contact = db.get(Key(encoded=self.request.get('contact_key')))
			oldfname = contact.firstname
			oldlname = contact.lastname
			oldemail = contact.email
			oldaddress = contact.address
			oldcity = contact.city
			oldstate = contact.state
			oldphone = contact.phone
			oldavatar = contact.avatar
			a = self.request.get('img')

			if self.request.get('firstname'):
				contact.firstname = self.request.get('firstname')
			else:
				contact.firstname = oldfname
			if self.request.get('lastname'):
				contact.lastname = self.request.get('lastname')
			else:
				contact.lastname = oldlname
			if self.request.get('email'):
				contact.email = self.request.get('email')
			else:
				contact.email = oldemail
			if self.request.get('address'):
				contact.address = self.request.get('address')
			else:
				contact.address = oldaddress
			if self.request.get('city'):
				contact.city = self.request.get('city')
			else:
				contact.city = oldcity
			if self.request.get('state'):
				contact.state = self.request.get('state')
			else:
				contact.state = oldstate
			if self.request.get('phone'):
				contact.phone = self.request.get('phone')
			else:
				contact.phone = oldphone
			if a:
				avatar = images.resize(a, 32, 32)
				contact.avatar = db.Blob(avatar)
			else:
				contact.avatar = oldavatar
			contact.put()
		
		self.redirect('/?' + urllib.urlencode({'contactlist_name': contactlist_name}))

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/sign', ContactList),
	('/img', Image),
	('/filter', Filter),
], debug=True)