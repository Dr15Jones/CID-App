import ui
import json
import dialogs

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
	other = 'other'
	@classmethod
	def categories(cls):
		#return (cls.beast,cls.jack,cls.other)
		return (cls.beast,cls.other)
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
	@property
	def category(self):
		return self.__type._category
	@category.setter
	def category(self,newCategory):
		self.__type._category = newCategory
		self.__cm.store_changes()

	def has_box(self,column,index):
		return (column, index) in self.__type._specialBoxes
	def add_box(self, column, index, active=False, label=None):
		self.__type._specialBoxes[(column,index)] =HitBoxQualities(active,label)
		self.__cm.store_changes()
	def remove_box(self,column, index):
		if (column,index) in self.__type._specialBoxes:
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
			del self.__model._hitBoxes[column,index]
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
# UI Controllers
#############################

class ListViewController(object):
	def __init__(self, listView, adderButton, itemViewController, delegate):
		self.__listView = listView
		self.__listView.data_source.edit_action = self.list_editted_action
		self.__listView.data_source.action = self.item_selected_action
		self.__itemViewController = itemViewController
		self.__itemViewController.name_change_callback = self.__selected_item_name_changed
		self.__delegate = delegate
		self.__lastSelectedRow = -1
		adderButton.action = self.add_new_item
		self.__update_list_ui()

	def add_new_item(self,sender):
		self.__delegate.add_new_item()
		self.__update_list_ui()

	def item_selected_action(self,sender):
		previousChoice = self.__itemViewController.name()
		#see if user was editting item name just
		# before changing the selected item
		newSelection = sender.selected_row
		if self.__lastSelectedRow != -1:
			oldName = self.__delegate.item_name(self.__lastSelectedRow)
			if oldName !=previousChoice:
				self.__delegate.set_item_name(self.__lastSelectedRow,previousChoice)
				self.__listView.data_source.items[self.__lastSelectedRow] = previousChoice
				self.__listView.reload()
		self.__lastSelectedRow = newSelection
		if -1 == newSelection:
			self.__itemViewController.disable()
		else:
			self.__itemViewController.edit_item(newSelection)

	def list_editted_action(self,sender):
		if self.__delegate.new_items_list(sender.items):
			#the selected item was probably deleted
			self.__itemViewController.disable()
		self.__lastSelectedRow = -1
		pass

	def __update_list_ui(self):
		self.__listView.data_source.items = self.__delegate.item_names()
		self.__listView.reload()

	def __selected_item_name_changed(self,newName):
		index = self.__listView.data_source.selected_row
		if -1 != index:
			self.__delegate.set_item_name(index,newName)
		self.__update_list_ui()

#############################
# Build Interface
#############################

class TypesDelegate(object):
	def __init__(self):
		pass
	def add_new_item(self):
		gDataSource.add_type(ModelType("New"))
	def item_name(self,index):
		return gDataSource.type(index).name
	def set_item_name(self,index,name):
		gDataSource.type(index).name = name
	def new_items_list(self, itemNames):
		return gDataSource.types_to_keep(itemNames)
	def item_names(self):
		return gDataSource.type_names()


class TypeEditorController(object):
	def __init__(self,editView):
		self.__editView = editView
		self.__nameView = editView['name']
		self.__nameView.action = self.__change_name_action
		self.__hitTypeView = editView['type']
		self.__hitTypeView.action = self.__change_hit_type_action
		self.disable()
		self.__hitControllerFactories = {BeastTypeHitController.categoryName():BeastTypeHitController,
			OtherTypeHitController.categoryName(): OtherTypeHitController}
		self.__hitController = None
	def edit_item(self,index):
		self.__index = index
		recursive_disabled(self.__editView,False)
		self.__nameView.text = gDataSource.type(index).name
		self.__switch_to_hit_type(gDataSource.type(index).category)
		pass
	@property
	def name_change_callback(self):
		return self.__name_change_callback
	@name_change_callback.setter
	def name_change_callback(self,action):
		self.__name_change_callback = action
	def disable(self):
		recursive_disabled(self.__editView,True)
		pass
	def __change_name_action(self,sender):
		self.__name_change_callback(sender.text)
	def __change_hit_type_action(self,sender):
		names = ModelType.categories()
		n = dialogs.list_dialog('Choose Hit Type',names)
		if not n :
			return
		gDataSource.type(self.__index).category = n
		self.__switch_to_hit_type(n)
		#self.__hitController.switch_model(self.__index)
	def __switch_to_hit_type(self,typeName):
		self.__hitTypeView.title = typeName
		hb = self.__editView['Hit Builder']
		if self.__hitController:
			hb.remove_subview(hb.subviews[0])
		self.__hitController = self.__hitControllerFactories[typeName](hb)
		self.__hitController.switch_type(self.__index)

	def name(self):
		return self.__nameView.text


def recursive_disabled(view,disable):
	view.hidden = disable


circleHitImage = ui.Image.named('iow:ios7_circle_filled_256')
circleNotHitImage = ui.Image.named('iow:ios7_circle_outline_256')

squareHitImage = None
squareNotHitImage = None
with ui.ImageContext(40,40) as ctx:
	sqr = ui.Path.rect(0,0,40,40)
	ui.set_color('black')
	sqr.line_width = 2
	sqr.stroke()
	squareNotHitImage = ctx.get_image()
	sqrt = ui.Path.rect(4,4,32,32)
	sqrt.fill()
	squareHitImage = ctx.get_image()

class SimpleTypeHitController(object):
	def __init__(self, hitsView):
		hitView = self.get_hit_view()
		hitView.flex = 'WH'
		self.__hitsView = hitsView
		hitView.height = hitsView.height
		hitView.width = hitsView.width
		hitsView.add_subview(hitView)
		hitsView.size_to_fit()
		self.__selectedType = -1
	
	def __enable_hit(self,hit):
		hit.alpha =1.
		hit.image = self.notHitImage
		hit.hit = False
	def __disable_hit(self,hit):
		hit.alpha =0.2
		hit.image = self.hitImage
		hit.hit = True

	def switch_type(self,index):
			self.__selectedType = index
			if index != -1:
				t = gDataSource.type(index)
				for s in self.__hitsView.subviews[0].subviews:
					if hasattr(s,"column"):
						if t.has_box(s.column,s.position):
							self.__disable_hit(s)
						else:
							self.__enable_hit(s)
			else:
				for s in self.__hitsView.subviews[0].subviews:
					if hasattr(s,"column"):
						self.__enable_hit(s)
			self.__hitsView.set_needs_display()

	def hit_action(self,sender):
		if self.__selectedType == -1:
			return
		if sender.hit:
			self.__enable_hit(sender)
			gDataSource.type(self.__selectedType).remove_box(sender.column,sender.position)
		else:
			self.__disable_hit(sender)
			gDataSource.type(self.__selectedType).add_box(sender.column,sender.position)


class BeastTypeHitController(SimpleTypeHitController):
	def __init__(self, hitsView):
		super(BeastTypeHitController,self).__init__(hitsView)
	def get_hit_view(self):
		#hit_pressed is looked for by the load_view
		global hit_pressed
		hit_pressed = self.hit_action
		hitView = ui.load_view("Beast Damage Marker")
		return hitView
	@property
	def hitImage(self):
		return circleHitImage
	@property
	def notHitImage(self):
		return circleNotHitImage
	@classmethod
	def categoryName(cls):
		return ModelType.beast

def create_other_hit_view(action):
	hitView = ui.View()
	for c in range(0,5):
		xoffset = 0
		position = 0
		for p in range(0,5):
			b = ui.Button()
			b.image = squareNotHitImage
			b.tint_color = 'red'
			b.frame=(xoffset,60*c,40,40)
			b.action = action
			b.column = c+1
			b.position = position
			xoffset += 40+10
			position +=1
			hitView.add_subview(b)
		xoffset += 30
		for p in range(0,5):
			b = ui.Button()
			b.image = squareNotHitImage
			b.tint_color = 'red'
			b.frame=(xoffset,60*c,40,40)
			b.action = action
			b.column = c+1
			b.position = position
			position +=1
			xoffset += 40+10
			hitView.add_subview(b)
	return hitView

class OtherTypeHitController(SimpleTypeHitController):
	def __init__(self, hitsView):
		super(OtherTypeHitController,self).__init__(hitsView)
	def get_hit_view(self):
		return create_other_hit_view(self.hit_action)
	@property
	def hitImage(self):
		return squareHitImage
	@property
	def notHitImage(self):
		return squareNotHitImage
	@classmethod
	def categoryName(cls):
		return ModelType.other



#############################
# Play Interface
#############################
class ModelsDelegate(object):
	def __init__(self):
		pass
	def add_new_item(self):
		t = gDataSource.type(0)
		gDataSource.add_model(Model(t,t.name+" "+str(len(gDataSource.model_names()))))
	def item_name(self,index):
		return gDataSource.model(index).name
	def set_item_name(self,index,name):
		gDataSource.model(index).name = name
	def new_items_list(self, itemNames):
		return gDataSource.models_to_keep(itemNames)
	def item_names(self):
		return gDataSource.model_names()


class ModelEditorController(object):
	def __init__(self,editView):
		self.__editView = editView
		self.__nameView = editView['name']
		self.__nameView.action = self.__change_name_action
		global add_model
		self.__hitControllerFactories = {BeastModelHitController.categoryName():BeastModelHitController,
				OtherModelHitController.categoryName():OtherModelHitController}
		self.__hitController = None #BeastModelHitController(editView['Hit Filler'])
		self.__typeChooserView = editView['type chooser']
		self.__typeChooserView.action = self.choose_type
		self.disable()
		self.__index = -1
	def edit_item(self,index):
		self.__index = index
		recursive_disabled(self.__editView,False)
		m =gDataSource.model(index)
		self.__nameView.text = m.name
		#setup hits
		self.__typeChooserView.title = m.type.name
		self.setup_model_type()
	#		setup_model_hit()
	@property
	def name_change_callback(self):
		return self.__name_change_callback
	@name_change_callback.setter
	def name_change_callback(self,action):
		self.__name_change_callback = action
	def disable(self):
		recursive_disabled(self.__editView,True)
		pass
	def __change_name_action(self,sender):
		if -1 != self.__index:
			#name must be unique
			name = sender.text
			model =gDataSource.model(self.__index)
			if name == model.name:
				return
			name = make_unique_model_name(name)
			if name != sender.text:
				sender.text = name
			self.__name_change_callback(sender.text)
	def name(self):
		return self.__nameView.text

	def choose_type(self, sender):
		names = gDataSource.type_names()
		n = dialogs.list_dialog('Type',names)
		if not n :
			return
		index = names.index(n)
		t =gDataSource.type(index)
		sender.title = t.name
		gDataSource.model(self.__index).type = t
		self.setup_model_type()
	def setup_model_type(self):
		hf = self.__editView['Hit Filler']
		if self.__hitController:
			hf.remove_subview(hf.subviews[0])
		t = gDataSource.model(self.__index).type
		self.__hitController = self.__hitControllerFactories[t.category](hf)
		self.__hitController.switch_model(self.__index)


class SimpleModelHitController(object):
	def __init__(self, hitsView):
		#hit_pressed is looked for by the load_view
		hitView = self.get_hit_view()
		#global hit_pressed
		#hit_pressed = self.hit_action
		#hitView = ui.load_view("Beast Damage Marker")
		hitView.flex = 'WH'
		self.__hitsView = hitsView
		hitView.height = hitsView.height
		hitView.width = hitsView.width
		hitsView.add_subview(hitView)
		hitsView.size_to_fit()
		self.__selectedModel = -1
		#self.__hitImage= ui.Image.named('iow:ios7_circle_filled_256')
		#self.__notHitImage= ui.Image.named('iow:ios7_circle_outline_256')
	
	def __enable_hit(self,hit):
		hit.hidden =False
		hit.alpha = 1.
		hit.image = self.notHitImage
		hit.hit = False
	def __disable_hit(self,hit):
		hit.hidden = True
		hit.alpha = 1.
		hit.image = self.notHitImage
		hit.hit = False
	def set_hit(self,hit):
		hit.image = self.hitImage
		hit.hit = True
	def set_unhit(self,hit):
		hit.image = self.notHitImage
		hit.hit = False

	def switch_model(self,index):
		self.__selectedModel = index
		model = gDataSource.model(index)
		mType = model.type
		for s in self.__hitsView.subviews[0].subviews:
			if hasattr(s,"column"):
				if mType.has_box(s.column,s.position):
					self.__disable_hit(s)
				else:
					self.__enable_hit(s)
					if model.was_hit(s.column,s.position):
						self.set_hit(s)
					else:
						self.set_unhit(s)
		self.__hitsView.set_needs_display()

	def hit_action(self,sender):
		if self.__selectedModel == -1:
			return
		if sender.hit:
			self.set_unhit(sender)
			gDataSource.model(self.__selectedModel).remove_hit(sender.column,sender.position)
		else:
			self.set_hit(sender)
			gDataSource.model(self.__selectedModel).add_hit(sender.column,sender.position)

def make_unique_model_name(name):
	while name in gDataSource.model_names():
		name += ' 1'
	return name

class OtherModelHitController(SimpleModelHitController):
	def __init__(self, hitsView):
		super(OtherModelHitController,self).__init__(hitsView)
	def get_hit_view(self):
		return create_other_hit_view(self.hit_action)
	@property
	def hitImage(self):
		return squareHitImage
	@property
	def notHitImage(self):
		return squareNotHitImage
	@classmethod
	def categoryName(cls):
		return ModelType.other

class BeastModelHitController(SimpleModelHitController):
	def __init__(self, hitsView):
		super(BeastModelHitController,self).__init__(hitsView)
	def get_hit_view(self):
		#hit_pressed is looked for by the load_view
		global hit_pressed
		hit_pressed = self.hit_action
		hitView = ui.load_view("Beast Damage Marker")
		return hitView
	@property
	def hitImage(self):
		return circleHitImage
	@property
	def notHitImage(self):
		return circleNotHitImage
	@classmethod
	def categoryName(cls):
		return ModelType.beast


hit_pressed = None

buildButton = None
playButton = None
modeView = None
mainView = None
runningView = None
notselected = '#808080'

gTypesController = None

add_model = None

def build_pressed(sender):
	global runningView
	if runningView:
		mainView.remove_subview(runningView)
	runningView = ui.load_view('Build')
	runningView.flex='WH'
	mainView.add_subview(runningView)
	runningView.height=mainView.height
	runningView.width=mainView.width

	sender.tint_color = None
	playButton.tint_color =notselected
	
	gTypesController = ListViewController(runningView['left']['Model Types'],
																				runningView['left']['Add Type'],
																				TypeEditorController(runningView['main']),
																				TypesDelegate())


gModelsController = None
def play_pressed(sender):
	global runningView
	if runningView:
		mainView.remove_subview(runningView)
	runningView = ui.load_view('Play')
	runningView.flex='WH'
	mainView.add_subview(runningView)
	runningView.height=mainView.height
	runningView.width=mainView.width

	sender.tint_color = None
	buildButton.tint_color = notselected

	gModelsController = ListViewController(runningView['left']['Models'],
																				 runningView['left']['Add Type'],
																				 ModelEditorController(runningView['main']),
																				 ModelsDelegate()
																				 )

gDataSource.retrieve_changes()
v = ui.load_view()
mainView=v['Main']
buildButton=v['bottom']['mode buttons']['Build']
playButton=v['bottom']['mode buttons']['Play']

build_pressed(buildButton)
v.present('fullscreen')
