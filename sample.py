import wx
from wxpython_react import  render, createComponent, Component


import datetime

class HumanClock(Component):
    def getInitialState(self):
        return {'time': datetime.datetime.now() }

    def componentDidMount(self):
        print "HC#componentDidMount"
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(1000)
    def componentWillUnmount(self):
        print "HC#componentWillUnmount"
        self.timer.Destroy()

    def onTimer(self, event):
        print "HC2#onTimer"
        self.setState({
            'time': datetime.datetime.now()
        })
    def render(self):
        print "HC#render %s" % self.state['time']
        return createComponent(wx.StaticText, {
            'label': "Time now: %s" % self.state['time'].strftime('%Y-%m-%d %H:%M:%S'), 
            'pos': (0,0), 
            'size': (100, 25)
        })

class app2(Component):
    def getInitialState(self):
        return { 'iter': 1, 'time': 0, 'closed': False }
    def componentDidMount(self):
        print "app#componentDidMount"
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(500)

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
    def onClose(self, event):
        print "app2#onClose"
        self.setState({
            'closed': True
        })
    def render(self):
        odd = self.state['iter'] % 2
        if self.state['closed']:
            return None
        return (
            createComponent(wx.Frame, {'shown': True, 'title': (odd and 'Dupa' or 'Blada'), 'onClose': self.onClose},
                createComponent(wx.Panel, {'backgroundColor': (odd and 'blue' or 'green'), 'size': (500, 500)},
                    (odd and
                        createComponent(wx.StaticText, {'label': "Hello world", 'pos': (25,25), 'onClick': self.onToggleTitle})
                    ),
                    (not odd and 
                        createComponent(wx.Button, { 'label': "Hello world", 'pos': (25,25), 'onClick': self.onToggleTitle })
                    ),
                    createComponent(wx.TextCtrl, { 'value': "Hello world\nLorem Ipsum", 'pos': (25, 50), 'size': (400, 200) }),
                    createComponent(wx.StaticText, {'label': 'time %s' % self.state['time'], 'pos': (25,275)}),
                    createComponent(HumanClock, {})
                )
            )
        )

a = wx.App()
render(a, createComponent(app2, { 'title': "Hello"}))
a.MainLoop()
 
