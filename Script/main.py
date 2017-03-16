import ui
import json

#############################
# Building Types
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
gKnownTypes = [ModelType('New')]

def recursive_disabled(view,disable):
	view.hidden = disable
		
def remove_all_models_of_type(type):
	global gKnownModels
	gKnownModels = [ x for x in gKnownModels if x._type != type]
	
def type_edit_action(sender):
	global gKnownTypes
	global runningView
	global list_last_selected_row
	global listView
	d = { x._name:x for x in gKnownTypes}
	gKnownTypes = []
	newNames = set()
	for n in sender.items:
		gKnownTypes.append(d[n])
		newNames.add(n)
	if len(gKnownTypes) < len(d):
		#the selected item was probably deleted
		recursive_disabled(runningView['main'],True)
		for n in d.keys():
			if n not in newNames:
				remove_all_models_of_type(d[n])
		#TODO: Should remove any model's using the removed Type
	store_changes()
	list_last_selected_row = -1

def update_type_list_ui():
	global listView
	listView.data_source.items = [ x._name for x in gKnownTypes]
	listView.reload()

list_last_selected_row = -1

def type_chosen(sender):
	global runningView
	global list_last_selected_row
	nameView = runningView['main']['name']
	previousChoice = nameView.text
	newSelection = sender.selected_row
	if list_last_selected_row != -1:
		if listView.data_source.items[list_last_selected_row] != previousChoice:
			listView.data_source.items[list_last_selected_row] = previousChoice
			gKnownTypes[list_last_selected_row]._name = previousChoice
			listView.reload()
	list_last_selected_row = newSelection
	if -1 == newSelection:
		recursive_disabled(runningView['main'],True)
	else:
		recursive_disabled(runningView['main'],False)
		nameView.text = gKnownTypes[newSelection]._name
		setup_build_hit()
				
	#runningView['main'].set_needs_display()

def change_type_name(sender):
	global listView
	index = listView.data_source.selected_row
	if -1 != index:
		gKnownTypes[index]._name = sender.text
	update_type_list_ui()
	store_changes()

		

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
			qualities = gKnownTypes[index]._specialBoxes
			for s in hitsView.subviews[0].subviews:
				if hasattr(s,"column"):
					if (s.column,s.position) in qualities:
						build_set_hit_disabled(s)
					else:
						build_set_hit_enabled(s)
		else:
			for s in hitsView.subviews[0].subviews:
				if hasattr(s,"column"):
					build_set_hit_enabled()
		hitsView.set_needs_display()
			
def build_hit_pressed(sender):
	global gKnownTypes
	index = listView.data_source.selected_row	
	if index == -1:
		return
	if sender.hit:
		build_set_hit_enabled(sender)
		key = (sender.column,sender.position)
		if key in gKnownTypes[index]._specialBoxes:
			del gKnownTypes[index]._specialBoxes[key]
	else:
		build_set_hit_disabled(sender)
		#disable it	
		#disable it	
		gKnownTypes[index]._specialBoxes[(sender.column,sender.position)]=HitBoxQualities(active=False)
	store_changes()

#############################
# Playing
#############################
class Model (object):
	def __init__(self,type,name,hits=None):
		self._name = name
		self._type = type
		if hits:
			self._hitBoxes =hits
		else:
			self._hitBoxes = {}

gKnownModels =[]

def model_edit_action(sender):
	global gKnownModels
	global runningView
	global list_last_selected_row
	global listView
	d = { x._name:x for x in gKnownModels}
	gKnownModels = []
	for n in sender.items:
		gKnownModels.append(d[n])
	if len(gKnownModels) < len(d):
		#the selected item was probably deleted
		recursive_disabled(runningView['main'],True)
	store_changes()
	list_last_selected_row = -1

def update_model_list_ui():
	global listView
	listView.data_source.items = [ x._name for x in gKnownModels]
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
			gKnownModels[list_last_selected_row]._name=previousChoice
			listView.reload()
	list_last_selected_row = newSelection
	if -1 == newSelection:
		recursive_disabled(runningView['main'],True)
	else:
		recursive_disabled(runningView['main'],False)
		nameView.text = gKnownModels[newSelection]._name
		runningView['main']['type chooser'].title = gKnownModels[newSelection]._type._name
		setup_model_hit()		

def make_unique_model_name(name):
	while name in [x._name for x in gKnownModels]:
		name += ' 1'
	return name

def change_model_name(sender):
	global listView
	index = listView.data_source.selected_row
	if -1 != index:
		#name must be unique
		name = sender.text
		if name == gKnownModels[index]._name:
			return
		name = make_unique_model_name(name)
		gKnownModels[index]._name = name
		if name != sender.text:
			sender.text = name
	update_model_list_ui()
	store_changes()

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
	model = gKnownModels[index]
	qualities = model._type._specialBoxes
	hits = model._hitBoxes
	hitsView = runningView['main']['Hit Filler']
	for s in hitsView.subviews[0].subviews:
		if hasattr(s,"column"):
			if (s.column,s.position) in qualities:
				play_set_hit_disabled(s)
			else:
				play_set_hit_enabled(s)
			if (s.column,s.position) in hits:
				play_set_hit(s)
			else:
				play_set_unhit(s)
						
def play_hit_pressed(sender):
	index = listView.data_source.selected_row
	if sender.hit:
		sender.hit = False
		sender.image = notHitImage
		key = (sender.column,sender.position)
		if key in gKnownModels[index]._hitBoxes:
			del gKnownModels[index]._hitBoxes[key]
	else:
		sender.hit = True
		sender.image = hitImage
		gKnownModels[index]._hitBoxes[(sender.column,sender.position)] = True
	store_changes()
		
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

def add_type(sender):
	global gKnownTypes
	gKnownTypes.append(ModelType("New"))
	update_type_list_ui()
	#note I can not get the new row selected
		
def add_model(sender):
	global gKnownModels
	t = gKnownTypes[0]
	gKnownModels.append(Model(t,t._name+" "+str(len(gKnownModels))))
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
	ls = ui.ListDataSource([t._name for t in gKnownTypes])
	v.data_source= ls
	v.delegate = ls
	cd = ChoiceDelegate(v)
	ls.action = cd.delegate
	#v.size_to_fit()
	v.present('sheet')
	v.wait_modal()
	if cd._choice != -1:
		sender.title = gKnownTypes[cd._choice]._name
		gKnownModels[listView.data_source.selected_row]._type = gKnownTypes[cd._choice]
		store_changes()
		setup_model_hit()

def store_changes():
	f = open(".cid","w")
	#version number
	jd = {}
	types =[]
	for t in gKnownTypes:
		type = { "name":t._name, "category":t._category, "boxes":[(b[0],b[1]) for b in t._specialBoxes.keys()]}
		types.append(type)
	jd["Types"]=types
	
	models =[]
	for m in gKnownModels:
		model = {"name":m._name, "type":m._type._name, "hits": [(h[0],h[1]) for h in m._hitBoxes.keys()]}
		models.append(model)		
	jd["Models"] = models
	f.write(json.dumps(jd))

def retrieve_changes():
	global gKnownTypes
	global gKnownModels
	try:
		f = open('.cid','r')
		gKnownTypes =[]
		gKnownModels = []
		js = json.loads(f.readline())

		nameToType ={}
		for t in js['Types']:
			name = t['name']
			category = t['category']
			boxes = t['boxes']
			gKnownTypes.append(ModelType(name,category, { (b[0],b[1]):HitBoxQualities() for b in boxes}))
			nameToType[name]=gKnownTypes[-1]
		for m in js['Models']:
			name = m['name']
			type = m['type']
			hits = m['hits']
			gKnownModels.append(Model(nameToType[type],name,{ (h[0],h[1]):True for h in hits}))
	except IOError:
		pass

retrieve_changes()
v = ui.load_view()
mainView=v['Main']
buildButton=v['bottom']['mode buttons']['Build']
playButton=v['bottom']['mode buttons']['Play']

build_pressed(buildButton)
v.present('fullscreen')
