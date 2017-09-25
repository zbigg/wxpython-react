# React wxPython

This is very experimental attempt to check if React approach is portable to
different programming environment:

 - other language *Python*
 - native *desktop*
 
## Current status:

 - naive, always-re-render-everything render and update loop works for wx.Frame, wx.Panel, wx.StaticText and wx.Button
 - API similar to `React.js`
   - createComponent
   - stateful component with `setState()` and typical callbacks
   - functional components
   - no context yet, but easy to add
 - no JSX counterpart or even idea how to approach this

## Running sample:

```
   apt-get install python-wxgtk3.0
   python sample.py
```

Have fun.
