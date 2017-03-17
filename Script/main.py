import ui
import json

#############################
# Data Model
#############################
class HitBoxQualities(object):
	def __init__(self, active = False, label = None):
		self._active = active
		self._label = label

class ModelType (object):
	beast = 'beast'
	jack = 'jack'
	def __init__(self, name,category=beast,specialBoxes=None):
		self._name = name
		self._category = category
		if specialBoxes:
			self._specialBoxes = specialBoxes
		else:
			self._specialBoxes = {}

class ModelTypeProxy(object):
	def __init__(self,changeManager, type):
		self.__cm = changeManager
		self.__type = type
	@property
	def name(self):
		return self.__type._name
	@name.setter
	def name(self,newName):
		self.__type._name = newName
		self.__cm.store_changes()

	def has_box(self,column,index):
		return (column, index) in self.__type._specialBoxes
	def add_box(self, column, index, active=False, label=None):
		self.__type._specialBoxes[(column,index)] =HitBoxQualities(active,label)
		self.__cm.store_changes()
	def remove_box(self,column, index):
		if (column,index) in self._specialBoxes:
			del self.__type._specialBoxes[(column,index)]
			self.__cm.store_changes()

class Model (object):
	def __init__(self,type,name,hits=None):
		self._name = name
		self._type = type
		if hits:
			self._hitBoxes =hits
		else:
			self._hitBoxes = {}


class ModelProxy(object):
	def __init__(self,changeManager, model):
		self.__model = model
		self.__cm = changeManager
	@property
	def name(self):
		return self.__model._name
	@name.setter
	def name(self,newName):
		self.__model._name = newName
		self.__cm.store_changes()
	@property
	def type(self):
		return self.__model._type
	@type.setter
	def type(self,t):
		self.__model._type = t
		self.__cm.store_changes()
	def was_hit(self,column,index):
		return (column,index) in self.__model._hitBoxes
	def add_hit(self,column,index):
		self.__model._hitBoxes[(column,index)] = True
		self.__cm.store_changes()
	def remove_hit(self,column,index):
		if (column,index) in self.__model._hitBoxes:
			del self.__model.hitBoxes[column,index]
			self.__cm.store_changes()

class DataSource(object):
	"""
		Contains the Model types and model instances in use
	"""
	def __init__(self):
		self._types = [ModelType('New')]
		self._models = []
		self._fileName = ".cid"

	def type(self,index):
		return ModelTypeProxy(self,self._types[index])

	def type_names(self):
		return [ x._name for x in self._types]

	def types_to_keep(self,typeNameList):
		returnValue= False
		d = { x._name:x for x in self._types}
		self._types = []
		newNames = set()
		for n in typeNameList:
			self._types.append(d[n])
			newNames.add(n)
		if len(self._types) < len(d):
			returnValue = True
			#the selected item was probably deleted
			for n in d.keys():
				if n not in newNames:
					self.__remove_all_models_of_type(d[n])
			self.store_changes()
		return returnValue

	def add_type(self,type):
		self._types.append(type)
		self.store_changes()

	def __remove_all_models_of_type(self,type):
		self._models = [ x for x in self._models if x._type != type]

	def model(self,index):
		return ModelProxy(self,self._models[index])
	
	def add_model(self,model):
		self._models.append(model)
		self.store_changes()

	def model_names(self):
		return [ x._name for x in self._models]
	
	def models_to_keep(self,modelNameList):
		returnValue= False
		d = { x._name:x for x in self._models}
		self._models = []
		for n in modelNameList:
			self._models.append(d[n])
		if len(self._models) < len(d):
			returnValue = True
			#the selected item was probably deleted
			self.store_changes()
		return returnValue


	def store_changes(self):
		f = open(self._fileName,"w")
		#version number
		jd = {}
		types =[]
		for t in self._types:
			type = { "name":t._name, "category":t._category, "boxes":[(b[0],b[1]) for b in t._specialBoxes.keys()]}
			types.append(type)
		jd["Types"]=types

		models =[]
		for m in self._models:
			model = {"name":m._name, "type":m._type.name, "hits": [(h[0],h[1]) for h in m._hitBoxes.keys()]}
			models.append(model)
		jd["Models"] = models
		f.write(json.dumps(jd))

	def retrieve_changes(self):
		try:
			f = open(self._fileName,'r')
			self._types =[]
			self._models = []
			js = json.loads(f.readline())

			nameToTypeIndex ={}
			for t in js['Types']:
				name = t['name']
				category = t['category']
				boxes = t['boxes']
				self._types.append(ModelType(name,category, { (b[0],b[1]):HitBoxQualities() for b in boxes}))
				nameToTypeIndex[name]=len(self._types)-1
			for m in js['Models']:
				name = m['name']
				type = m['type']
				hits = m['hits']
				self._models.append(Model(self.type(nameToTypeIndex[type]),name,{ (h[0],h[1]):True for h in hits}))
		except IOError:
			pass

gDataSource = DataSource()


#############################
# Build Interface
#############################

def recursive_disabled(view,disable):
	view.hidden = disable

def type_edit_action(sender):
	global gDataSource
	global runningView
	global list_last_selected_row
	if gDataSource.types_to_keep(sender.items):
		#the selected item was probably deleted
		recursive_disabled(runningView['main'],True)
	list_last_selected_row = -1

def update_type_list_ui():
	global listView
	listView.data_source.items = gDataSource.type_names()
	listView.reload()

list_last_selected_row = -1

def type_chosen(sender):
	global runningView
	global list_last_selected_row
	nameView = runningView['main']['name']
	previousChoice = nameView.text
	newSelection = sender.selected_row
	if list_last_selected_row != -1:
		t =gDataSource.type(list_last_selected_row)
		if t.name !=previousChoice:
			t.name = previousChoice
			listView.data_source.items[list_last_selected_row] = previousChoice
			listView.reload()
	list_last_selected_row = newSelection
	if -1 == newSelection:
		recursive_disabled(runningView['main'],True)
	else:
		recursive_disabled(runningView['main'],False)
		nameView.text = gDataSource.type(newSelection).name
		setup_build_hit()
				
	#runningView['main'].set_needs_display()

def change_type_name(sender):
	global listView
	index = listView.data_source.selected_row
	if -1 != index:
		gDataSource.type(index).name = sender.text
	update_type_list_ui()

		

hitImage = ui.Image.named('iow:ios7_circle_filled_256')
notHitImage = ui.Image.named('iow:ios7_circle_outline_256')

def build_set_hit_enabled(hit):
	hit.alpha =1.
	hit.image = notHitImage
	hit.hit = False

def build_set_hit_disabled(hit):
	hit.alpha =0.2
	hit.image = hitImage
	hit.hit = True
	
def setup_build_hit():
		index = listView.data_source.selected_row
		hitsView = runningView['main']['Hit Builder']
		if index != -1:
			t = gDataSource.type(index)
			for s in hitsView.subviews[0].subviews:
				if hasattr(s,"column"):
					if t.has_box(s.column,s.position):
						build_set_hit_disabled(s)
					else:
						build_set_hit_enabled(s)
		else:
			for s in hitsView.subviews[0].subviews:
				if hasattr(s,"column"):
					build_set_hit_enabled()
		hitsView.set_needs_display()
			
def build_hit_pressed(sender):
	global gDataSource
	index = listView.data_source.selected_row	
	if index == -1:
		return
	if sender.hit:
		build_set_hit_enabled(sender)
		gDataSource.type(index).remove_box(sender.column,sender.position)
	else:
		build_set_hit_disabled(sender)
		gDataSource.type(index).add_box(sender.column,sender.position)

def add_type(sender):
	global gDataSource
	gDataSource.add_type(ModelType("New"))
	update_type_list_ui()
	#note I can not get the new row selected


#############################
# Play Interface
#############################

def model_edit_action(sender):
	global gDataSource
	global runningView
	global list_last_selected_row
	if gDataSource.models_to_keep(sender.items):
		#the selected item was probably deleted
		recursive_disabled(runningView['main'],True)
	list_last_selected_row = -1

def update_model_list_ui():
	global listView
	listView.data_source.items = gDataSource.model_names()
	listView.reload()

def model_chosen(sender):
	global runningView
	global list_last_selected_row
	nameView = runningView['main']['name']
	previousChoice = nameView.text
	newSelection = sender.selected_row
	if list_last_selected_row != -1:
		#might have selected a new row without first hitting return in the name text field
		if listView.data_source.items[list_last_selected_row] != previousChoice:
			listView.data_source.items[list_last_selected_row] = previousChoice
			gDataSource.model(list_last_selected_row).name=previousChoice
			listView.reload()
	list_last_selected_row = newSelection
	if -1 == newSelection:
		recursive_disabled(runningView['main'],True)
	else:
		recursive_disabled(runningView['main'],False)
		m =gDataSource.model(newSelection)
		nameView.text = m.name
		runningView['main']['type chooser'].title = m.type.name
		setup_model_hit()		

def make_unique_model_name(name):
	while name in gDataSource.model_names():
		name += ' 1'
	return name

def change_model_name(sender):
	global listView
	index = listView.data_source.selected_row
	if -1 != index:
		#name must be unique
		name = sender.text
		model =gDataSource.model(index)
		if name == model.name:
			return
		name = make_unique_model_name(name)
		model.name = name
		if name != sender.text:
			sender.text = name
	update_model_list_ui()

def play_set_hit_enabled(hit):
	hit.hidden =False
	hit.alpha = 1.
	hit.image = notHitImage
	hit.hit = False

def play_set_hit_disabled(hit):
	hit.hidden = True
	hit.alpha = 1.
	hit.image = notHitImage
	hit.hit = False

def play_set_hit(hit):
	hit.image = hitImage
	hit.hit = True

def play_set_unhit(hit):	
	hit.image = notHitImage
	hit.hit = False

def setup_model_hit():
	index = listView.data_source.selected_row
	model = gDataSource.model(index)
	mType = model.type
	hitsView = runningView['main']['Hit Filler']
	for s in hitsView.subviews[0].subviews:
		if hasattr(s,"column"):
			if mType.has_box(s.column,s.position):
				play_set_hit_disabled(s)
			else:
				play_set_hit_enabled(s)
			if model.was_hit(s.column,s.position):
				play_set_hit(s)
			else:
				play_set_unhit(s)
						
def play_hit_pressed(sender):
	index = listView.data_source.selected_row
	if sender.hit:
		sender.hit = False
		sender.image = notHitImage
		gDataSource.model(index).remove_hit(sender.column,sender.position)
	else:
		sender.hit = True
		sender.image = hitImage
		gDataSource.model(index).add_hit(sender.column,sender.position)

hit_pressed = None

buildButton = None
playButton = None
modeView = None
mainView = None
runningView = None
listView = None
notselected = '#808080'
def build_pressed(sender):
	global runningView
	global listView
	global list_last_selected_row
	list_last_selected_row = -1
	if runningView:
		mainView.remove_subview(runningView)
	runningView = ui.load_view('Build')
	runningView.flex='WH'
	mainView.add_subview(runningView)
	runningView.height=mainView.height
	runningView.width=mainView.width
	runningView['main']['name'].action = change_type_name
	recursive_disabled(runningView['main'], True)
	listView = runningView['left']['Model Types']
	update_type_list_ui()
	listView.data_source.edit_action = type_edit_action
	listView.data_source.action = type_chosen
	sender.tint_color = None
	playButton.tint_color =notselected
	
	#hit_pressed has to be set before loading the view
	hit_pressed = build_hit_pressed	
	hitView = ui.load_view("Beast Damage Marker")
	hitView.flex = 'WH'
	buildView = runningView['main']['Hit Builder']
	hitView.height = buildView.height
	hitView.width = buildView.width
	buildView.add_subview(hitView)
	buildView.size_to_fit()

		
def play_pressed(sender):
	global runningView
	global listView
	global list_last_selected_row
	list_last_selected_row = -1
	if runningView:
		mainView.remove_subview(runningView)
	runningView = ui.load_view('Play')
	runningView.flex='WH'
	mainView.add_subview(runningView)
	runningView.height=mainView.height
	runningView.width=mainView.width
	runningView['main']['name'].action = change_model_name
	recursive_disabled(runningView['main'],True)
	listView = runningView['left']['Models']
	update_model_list_ui()
	listView.data_source.edit_action = model_edit_action
	listView.data_source.action = model_chosen
	
	sender.tint_color = None
	buildButton.tint_color = notselected

	#hit_pressed has to be set before loading the view
	hit_pressed = play_hit_pressed	
	hitView = ui.load_view("Beast Damage Marker")
	hitView.flex = 'WH'
	hitView.height = mainView.height
	hitView.width  = mainView.width
	runningView['main']['Hit Filler'].add_subview(hitView)

def add_model(sender):
	global gDataSource
	t = gDataSource.type(0)
	gDataSource.add_model(Model(t,t.name+" "+str(len(gDataSource.model_names()))))
	update_model_list_ui()
	pass
	
class ChoiceDelegate (object):
	def __init__(self,view):
		self._choice = -1
		self._view = view
	def delegate(self,sender):
		self._choice= sender.selected_row
		self._view.close()
		

def choose_type(sender):
	v = ui.TableView()
	v.allows_selection=True
	v.set_editing=False
	ls = ui.ListDataSource(gDataSource.type_names())
	v.data_source= ls
	v.delegate = ls
	cd = ChoiceDelegate(v)
	ls.action = cd.delegate
	#v.size_to_fit()
	v.present('sheet')
	v.wait_modal()
	if cd._choice != -1:
		t =gDataSource.type(cd._choice)
		sender.title = t.name
		gDataSource.model(listView.data_source.selected_row).type = t
		setup_model_hit()

gDataSource.retrieve_changes()
v = ui.load_view()
mainView=v['Main']
buildButton=v['bottom']['mode buttons']['Build']
playButton=v['bottom']['mode buttons']['Play']

build_pressed(buildButton)
v.present('fullscreen')
