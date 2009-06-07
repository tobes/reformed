import reformed.dbconfig as dbconfig
import reformed.reformed as r
from sqlalchemy.orm import eagerload



class FormCache(object):

	instance = None
	form_cache = {}
	form_names = {}
			
	def __new__(self):
	
		"""singleton"""
		
		if not self.instance:
			self.instance = object.__new__(self)
		return self.instance


	def _get_form_names(self):

		form_names = {}
		session = dbconfig.Session()
		data = session.query(r.reformed.get_class('form')).options()
		for row in data:
			self.form_names[row.name] = int(row.id)
		session.close()
			
			
	def reset(self):
	
		"""reset the cache"""
		
		self.form_cache = {}
		self._get_form_names()	
		
	def get_form(self, form_id):
	
		""" get the form info """

		if not self.form_cache.has_key(form_id):
			# not in the cache need to get the data
			self.form_cache[form_id] = self.Form(form_id)
			
		return self.form_cache[form_id]


	def get_id_from_name(self, form_name):
	
		if self.form_names.has_key(form_name):
			return self.form_names[form_name]
		else:
			return 0
	
	
	class Form(object):

		def __init__(self, form_name):

			self.form_items = []
			self.subforms = {}
			session = dbconfig.Session()
			self.form = session.query(r.reformed.get_class('form')).options(eagerload('form_param')).filter_by(name=form_name).one()
			form_id = self.form.id
			# params (form)
			self.form_params = self._get_params( self.form.form_param )
			
			form_items = session.query(r.reformed.get_class('form_item')).options(eagerload('form_item_param')).filter_by(form_id=form_id, active=True).order_by(r.reformed.get_class('form_item').sort_order)
			# params (form_item)
			for form_item in form_items:
				item = self.FormItem(form_item, self._get_params(form_item.form_item_param))
				self.form_items.append(item)
				if form_item.item == 'subform':
					if item.params('subform_name'):
						self.subforms[form_item.name] = item.params('subform_name')
			session.close()
			

		def _get_params(self, item_list):
	
			""" helper function to transform list into __dict__ 
				doesn't python have a natural way to do this?? """
			
			params = {}
			for p in item_list:
				if p.key:
					params[str(p.key)] = str(p.value)
			return params

		def params(self, param):

			"""helper function to return form_param value or None if no such param"""
	
			if self.form_params.has_key(param):
				return self.form_params[param]
			else:
				return None
	
			

		class FormItem(object):
	
		
			def __init__(self, form_item, form_item_params):

				self.form_item = form_item
				self.form_item_params = form_item_params

			def __getattr__(self, item):
			
				if hasattr(self.form_item, item):
					return getattr(self.form_item, item)
				else:
					return None
				
			def params(self, param):

				"""helper function to return form_param value or None if no such param"""
	
				if self.form_item_params.has_key(param):
					return self.form_item_params[param]
				else:
					return None
				
				
		
