import pprint
import wx
from itertools import izip_longest

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

def rce(type, props, *children):
    return Bunch(type=type, children=children, props=props)

class Component:
    def setState(self, new_state):
        # TBD, new API with callbacks
        aboutToChangeState(self, dict(self.state, **new_state))

def app(props):
    print props
    return (
        rce(wx.Frame, { 'shown': True, 'title': props['title'] } ,
            rce(wx.Panel, { 'background_color': wx.GREEN }, 
                rce(wx.StaticText, { 'label': "Hello world", 'pos': (25,25) }),
                rce(wx.TextCtrl, { 'value': "Hello world\nLorem Ipsum", 'pos': (25, 55) })
            )
        )
    )

class app2(Component):
    def getInitialState(self):
        return { 'iter': 1, 'time': 0 }
    def componentDidMount(self):
        print "app#componentDidMount"
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(10)
    def componentWillUnmount(self):
        print "app#componentWillUnmount"
        
    def onTimer(self, event):
        print "app2#onTimer"
        self.setState({
            'time': self.state['time'] + 1
        })
    def onToggleTitle(self, event):
        print "app2#onToggleTitle"
        self.setState({
            'iter': ( self.state['iter'] + 1 )
        })
    def render(self):
        odd = self.state['iter'] % 2;
        return (
            rce(wx.Frame, {'shown': True, 'title': (odd and 'Dupa' or 'Blada')},
                rce(wx.Panel, {'background_color': (odd and 'blue' or 'green'), 'size': (500, 500)},
                    (odd and
                        rce(wx.StaticText, {'label': "Hello world", 'pos': (25,25), 'onClick': self.onToggleTitle})
                    ),
                    ( not odd and 
                        rce(wx.Button, { 'label': "Hello world", 'pos': (25,25), 'onClick': self.onToggleTitle })
                    ),
                    rce(wx.TextCtrl, { 'value': "Hello world\nLorem Ipsum", 'pos': (25, 50), 'size': (400, 200) }),
                    rce(wx.StaticText, {'label': 'time %s' % self.state['time'], 'pos': (25,275)})
                )
            )
        )

def destroy(element):
    if element is not None:
        element.Destroy()

def create_element(type, props, context):
    wx_parent = (context is not None and context.get_wx_parent()) or None
    r = type(wx_parent)
    apply_props(r, props)
    return r

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
    elif key == 'onClick':
        element.Bind(wx.EVT_LEFT_UP, value)
    elif key == 'background_color':
        element.SetBackgroundColour(value)
    else:
        pass


to_be_updated = []

def aboutToChangeState(self, new_state):
    self.next_state = new_state
    global to_be_updated
    to_be_updated.append(self)

def shouldComponentUpdate(instance, new_props):
    new_state = instance.next_state or instance.state
    #print "dvu %s -> %s" % (instance.state, new_state)
    if hasattr(instance, 'shouldComponentUpdate'):
        return instance.shouldComponentUpdate(new_props, new_state )
    else:
        return ( new_props != instance.props or new_state != instance.state )

def componentWillUnmount(vdom):
    instance = vdom.instance
    if vdom.rendered:
        if instanceof(vdom.rendered, 'list') or instanceof(vdom.rendered, 'tuple'):
            for child in vdom.rendered:
                componentWillUnmount(child)
        else:
            componentWillUnmount(vdom)
    if hasattr(instance, componentWillUnmount):
        instance.componentWillUnmount()
    else:
        return ( new_props != instance.props or new_state != instance.state)

def apply_props(element, props):
    for key, value in props.items():
        apply_prop(element, key, value)

current_root = None

def render_int(vdom_old, vdom_new, context):
    #print "#render %s -> %s" % (vdom_old, vdom_new)
    if not vdom_new or ( vdom_old and vdom_old.type != vdom_new.type ):
        if vdom_old:
            print "#render_int destroing something"
            if vdom_old.instance:
                componentWillUnmount(vdom_old)
            if vdom_old.wx_control:
                vdom_old.wx_control.Destroy()

    if not vdom_new:
        return

    just_mounted = False
    just_updated = False;
    if vdom_new is vdom_old:
        vdom_old = Bunch(**vdom_old)
    if issubclass(vdom_new.type, Component):
        instance = vdom_old and vdom_old.instance
        should_update = True
        if instance:
            should_update = shouldComponentUpdate(instance, vdom_new.props)
            #print "#shouldComponentUpdate %s -> %s" % (vdom_new.type, should_update)
            if should_update:
                if hasattr(instance, 'componentWillUpdate'):
                    instance.componentWillUpdate(vdom_new.props, instance.next_state)
                just_updated = True
            if instance.next_state:
                instance.state = instance.next_state
        else:
            just_mounted = True
            instance = vdom_new.type()
            instance.props = vdom_new.props
            instance.state = instance.getInitialState()
            if hasattr(instance, 'componentWillMount'):
                instance.componentWillMount()
            vdom_new.instance = instance
        if should_update:
            tmp_props = vdom_new.props.copy()
            tmp_props['children'] = vdom_new.children
            saved_props = instance.props
            instance.props = tmp_props
            instance.parent = context.parent
            vdom_new.rendered = instance.render()
            instance.props = saved_props

    elif hasattr(vdom_new.type, 'Create') and callable(vdom_new.type.Create):
        #print "#rrr %s %s" % (vdom_old, vdom_old and vdom_old.wx_control)
        if not vdom_old or not vdom_old.wx_control:
            #print "creating wx %s" % vdom_new.type
            constructor = vdom_new.type
            vdom_new.wx_control = constructor(context.wx_parent)
            apply_props(vdom_new.wx_control, vdom_new.props)
        else:
            vdom_new.wx_control = vdom_old.wx_control
            for prop_name, prop_value in vdom_new.props.items():
                if not prop_name in vdom_old.props:
                    apply_prop(vdom_new.wx_control, prop_name, prop_value)
                else:
                    old_prop_value = vdom_old.props[prop_name]
                    # print "?? %s vs %s" % (old_prop_value, prop_value)
                    if old_prop_value != prop_value:
                        apply_prop(vdom_new.wx_control, prop_name, prop_value)
    elif callable(vdom_new.type):
        #print "rendering functional %s" % vdom_new.type
        tmp_props = vdom_new.props.copy()
        tmp_props['children'] = vdom_new.children
        vdom_new.rendered = vdom_new.type(tmp_props)
    else:
        raise RuntimeError('invalid RCE type %s' % vdom_new.type)
    
    # now render actual children or render output
    rendered_children = vdom_new.rendered or vdom_new.children

    #print "#render, deep %s %s" % (rendered_children, not not rendered_children)
    if rendered_children is not None:
        child_context = Bunch(
            instance_parent = vdom_new.instance or context.instance,
            wx_parent = vdom_new.wx_control or context.wx_control
        )
        old_children = vdom_old and ( vdom_old.rendered or vdom_old.children )
        if isinstance(rendered_children, list) or isinstance(rendered_children, tuple):
            for new_child_vdom, old_child_vdom in izip_longest(rendered_children, old_children or [], ):
                render_int(old_child_vdom, new_child_vdom, child_context)
        else:
            render_int(old_children, rendered_children, child_context)

    if vdom_new.instance and just_updated:
        if hasattr(vdom_new.instance, 'componentDidUpdate'):
            vdom_new.instance.componentDidUpdate()
        
    if vdom_new.instance and just_mounted:
        if hasattr(vdom_new.instance, 'componentDidMount'):
            vdom_new.instance.componentDidMount()
    return vdom_new


current_vdom = None

def render(new_vdom):
    global to_be_updated
    to_be_updated = []
    print "render ..."
    global current_vdom
    render_int(current_vdom, new_vdom, Bunch(wx_control = None))
    current_vdom = new_vdom
    
pp = pprint.PrettyPrinter(depth=10)
#pp.pprint(app({}))

a = wx.App()
render(rce(app2, { 'title': "Hello"}))

def wx_idle(event):
    global to_be_updated
    if len(to_be_updated) > 0:
        render(current_vdom)

a.Bind(wx.EVT_IDLE, wx_idle)
a.MainLoop()
 
