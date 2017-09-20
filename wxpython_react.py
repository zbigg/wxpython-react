from itertools import izip_longest
import wx

class Bunch(dict):
    def __init__(self, **kwargs):
        super(Bunch, self).__init__(kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __dir__(self):
        return self.keys()

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setstate__(self, state):                                              
        pass

def createComponent(type, props, *children):
    return Bunch(type=type, children=tuple_or_list(children), props=props)

class Component:
    def init(self):
        self.state = None
        self.next_state = None

    def setState(self, new_state):
        # TBD, new API with callbacks
        aboutToChangeState(self, dict(self.state, **new_state))

def apply_prop(element, key, value):
    print "setting prop %s %s on %s" % (key, str(value), element)
    if   key == 'pos':
        element.SetPosition(value)
    elif key == 'size':
        element.SetSize(value)
    elif   key == 'shown':
        element.Show(value)
    elif   key == 'label':
        element.SetLabel(value)
    elif   key == 'value':
        element.SetValue(value)
    elif key == 'title':
        element.SetTitle(value)
    elif key == 'onClose':
        element.Bind(wx.EVT_CLOSE, value)
    elif key == 'onClick':
        element.Bind(wx.EVT_LEFT_UP, value)
    
    else:
        pass


to_be_updated = []

def aboutToChangeState(self, new_state):
    self.next_state = new_state
    global to_be_updated
    to_be_updated.append(self)

def shouldComponentUpdate(instance, new_props):
    new_state = hasattr(instance,'next_state') and instance.next_state or instance.state
    if hasattr(instance, 'shouldComponentUpdate'):
        return instance.shouldComponentUpdate(new_props, new_state)
    else:
        return (new_props != instance.props or new_state != instance.state)

def componentWillUnmount(vdom):
    if vdom.rendered:
        for child in tuple_or_list(vdom.rendered or vdom.children):
            componentWillUnmount(child)

    if vdom.instance and hasattr(vdom.instance, 'componentWillUnmount'):
        vdom.instance.componentWillUnmount()

def apply_props(element, props):
    for key, value in props.items():
        apply_prop(element, key, value)

class windowLikeAdapter:
    @classmethod
    def create(type, parent, props):
        r = type(parent)

    @classmethod
    def set_prop(wx_control, key, value):
        if   key == 'pos':
            wx_control.SetPosition(value)
        elif key == 'size':
            wx_control.SetSize(value)
        elif key == 'enabled':
            wx_control.SetEnabled(value)
        elif   key == 'shown' or key == 'show':
            wx_control.Show(value)
        elif key == 'backgroundColor':
            wx_control.SetBackgroundColour(value)
        elif key == 'border':
            wx_control.SetStyle((wx_control.GetStyle() & ~ wx.BORDER_MASK) | (
                wx.BORDER_SIMPLE if value == 'simple' else
                wx.BORDER_DOUBLE if value == 'double' else
                wx.BORDER_DEFAULT if value == 'default' else wx.BORDER_DEFAULT
            ))

class wxTopLevelAdapter(windowLikeAdapter):
    @classmethod
    def set_prop(wx_control, key, value):
        if key == 'title':
            wx_control.SetTitle(value)
        else:
            windowLikeAdapter.set_prop(wx_control, key, value)

class wxButtonAdapter(windowLikeAdapter):
    @classmethod
    def set_prop(wx_control, key, value):
        if key == 'onClick':
            wx_control.Bind(wx.EVT_BUTTON, value)
        else:
            windowLikeAdapter.set_prop(wx_control, key, value)

handlers = {}
handlers['window'] = windowLikeAdapter
handlers[wx.Window] = windowLikeAdapter

def tuple_or_list(obj):
    return (
        obj     if isinstance(obj, list) or isinstance(obj, tuple) else 
        []      if not obj  else
        [ obj ]
    )
#
# actual render
#   instantiate components, possibly rendering
#   recurses into rendered or direct children
# 
#
def render_int(vdom_old, vdom_new, context):
    #print "#render %s -> %s" % (vdom_old, vdom_new)
    if not vdom_new or (vdom_old and vdom_old.type != vdom_new.type):
        if vdom_old:
            componentWillUnmount(vdom_old)
            if vdom_old.wx_control:
                print "destroy on %s" % vdom_old.type
                vdom_old.wx_control.Destroy()


    just_mounted = False
    just_updated = False
    if vdom_new:
        if vdom_new is vdom_old:
            vdom_old = Bunch(**vdom_old)

        if issubclass(vdom_new.type, Component):
            # generic wxpython-react.Component
            instance = vdom_old and vdom_old.instance
            should_update = True
            if instance:
                # old one, check if update needed
                vdom_new.instance = instance
                should_update = shouldComponentUpdate(instance, vdom_new.props)
                if should_update:
                    if hasattr(instance, 'componentWillUpdate'):
                        instance.componentWillUpdate(vdom_new.props, instance.next_state)
                    just_updated = True
                if hasattr(instance, 'next_state'):
                    instance.state = instance.next_state
                    del instance.next_state
            else:
                #initialize new
                just_mounted = True
                instance = vdom_new.type()
                instance.props = vdom_new.props
                instance.state = instance.getInitialState()
                if hasattr(instance, 'componentWillMount'):
                    instance.componentWillMount()
                vdom_new.instance = instance
            if should_update:
                # render if new of should be updated
                tmp_props = vdom_new.props.copy()
                tmp_props['children'] = vdom_new.children
                saved_props = instance.props
                instance.props = tmp_props
                instance.parent = context.parent
                vdom_new.rendered = tuple_or_list(instance.render())
                # TBD, here we shall compare
                #  new vs old rendered (type + props + children) only
                #  and trigger rerender children only if difference is detected

                instance.props = saved_props
            else:
                vdom_new.rendered = vdom_old.rendered

        elif hasattr(vdom_new.type, 'Create') and callable(vdom_new.type.Create):
            # wxPython class
            if not vdom_old or not vdom_old.wx_control:
                constructor = vdom_new.type
                print "#create %s" % vdom_new.type
                vdom_new.wx_control = constructor(context.wx_parent)
                apply_props(vdom_new.wx_control, vdom_new.props)
            else:
                vdom_new.wx_control = vdom_old.wx_control
                for prop_name, prop_value in vdom_new.props.items():
                    if not prop_name in vdom_old.props:
                        apply_prop(vdom_new.wx_control, prop_name, prop_value)
                    else:
                        old_prop_value = vdom_old.props[prop_name]
                        if old_prop_value != prop_value:
                            apply_prop(vdom_new.wx_control, prop_name, prop_value)
        elif callable(vdom_new.type):
            # generic function object
            tmp_props = vdom_new.props.copy()
            tmp_props['children'] = vdom_new.children
            vdom_new.rendered = tuple_or_list( vdom_new.type(tmp_props) )
        else:
            raise RuntimeError('invalid RCE type %s' % vdom_new.type)
    
    # now render actual children or render output
    rendered_children = tuple_or_list(vdom_new and (vdom_new.rendered or vdom_new.children))
    old_children = tuple_or_list(vdom_old and (vdom_old.rendered or vdom_old.children))

    #print "#render before descend from %s into %s" % ( vdom_new and vdom_new.type, rendered_children,)
    if len(rendered_children) > 0 or len(old_children) > 0:
        child_context = vdom_new and Bunch(
            instance = (vdom_new and vdom_new.instance) or context.instance,
            wx_parent = (vdom_new and vdom_new.wx_control) or context.wx_parent
        )
        for new_child_vdom, old_child_vdom in izip_longest(rendered_children, old_children):
            render_int(old_child_vdom, new_child_vdom, child_context)
        
    if vdom_new and vdom_new.instance:
        if just_updated and hasattr(vdom_new.instance, 'componentDidUpdate'):
            vdom_new.instance.componentDidUpdate()
            
        if just_mounted and hasattr(vdom_new.instance, 'componentDidMount'):
            vdom_new.instance.componentDidMount()

    return vdom_new

the_app = None
current_vdom = None

def wx_idle(event):
    global to_be_updated
    if len(to_be_updated) > 0:
        _render(current_vdom)

def _render(vdom):
    global to_be_updated
    to_be_updated = []

    global current_vdom
    render_int(current_vdom, vdom, Bunch(wx_control = None))
    current_vdom = vdom

def render(app, vdom):
    _render(vdom)
    the_app = app
    app.Bind(wx.EVT_IDLE, wx_idle)
 

