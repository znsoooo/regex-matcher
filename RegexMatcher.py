import re

import wx
import wx.stc as stc

__ver__ = 'v1.0.0'


class MyTextCtrl(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'face:Courier New,size:11')
        self.StyleSetSpec(1, 'back:#FFFF00')
        self.SetAdditionalSelectionTyping(True)
        self.SetEOLMode(stc.STC_EOL_LF)  # fix save file '\r\n' translate to '\r\r\n'
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 30)
        self.SetMargins(5, -5)
        self.SetMultipleSelection(True)
        self.SetTabWidth(4)
        self.SetUseTabs(False)
        self.SetViewWhiteSpace(True)
        self.SetWrapMode(stc.STC_WRAP_CHAR)

        self.Bind(stc.EVT_STC_CHANGE, self.OnText)

        self.OnText(-1)

    def OnText(self, evt):
        lines = self.GetLineCount()
        width = len(str(lines)) * 9 + 5
        self.SetMarginWidth(1, width)

    def StartStyling(self, start):
        try:
            super().StartStyling(start)
        except TypeError:  # compatible for old version of wxPython
            super().StartStyling(start, 0xFFFF)


class Private:
    @property
    def text(self):
        return self.tc_text.GetValue()

    @text.setter
    def text(self, value):
        self.tc_text.SetValue(str(value))

    @property
    def result(self):
        return self.tc_res.GetValue()

    @result.setter
    def result(self, value):
        self.tc_res.SetValue(str(value))

    @property
    def pattern(self):
        return self.tc_patt.GetValue()

    @pattern.setter
    def pattern(self, value):
        self.tc_patt.SetValue(str(value))

    @property
    def replace(self):
        return self.tc_repl.GetValue()

    @replace.setter
    def replace(self, value):
        self.tc_repl.SetValue(str(value))


class MyPanel(Private):
    def __init__(self, parent):
        p1 = wx.Panel(parent)
        p2 = wx.Panel(parent)

        # - Add widgets --------------------

        self.tc_text = MyTextCtrl(p1)
        self.tc_res  = MyTextCtrl(p2)
        self.tc_patt = wx.TextCtrl(p2, size=(20, -1))
        self.tc_repl = wx.TextCtrl(p2, size=(20, -1))

        self.cb_sorted  = wx.CheckBox(p2, -1, 'Sorted')
        self.cb_unique  = wx.CheckBox(p2, -1, 'Unique')
        self.rb_regex   = wx.RadioButton(p2, -1, 'RegEx:', style=wx.RB_GROUP)
        self.rb_replace = wx.RadioButton(p2, -1, 'Replace:')

        self.bt_prev  = wx.Button(p2, -1, '<',     size=(24, 24))
        self.bt_next  = wx.Button(p2, -1, '>',     size=(24, 24))
        self.bt_apply = wx.Button(p2, -1, 'Apply', size=(24, 24))

        self.st_text = wx.StaticText(p1, -1, 'Text:')
        self.st_res  = wx.StaticText(p2, -1, 'Result:')

        # - Set layout --------------------

        gap = parent.GetSashSize()

        box1 = wx.BoxSizer(wx.VERTICAL)
        flags1 = wx.EXPAND | wx.TOP | wx.LEFT
        box1.Add(self.st_text, 0, flags1, gap)
        box1.Add(self.tc_text, 1, flags1, gap)
        box1.Add((0, 0),       0, flags1, gap)

        box21 = wx.BoxSizer()
        box21.Add(self.st_res,     1, wx.ALIGN_CENTER)
        box21.Add(self.cb_sorted,  0, wx.ALIGN_CENTER)
        box21.Add(self.cb_unique,  0, wx.ALIGN_CENTER)

        box22 = wx.GridBagSizer(vgap=gap, hgap=gap)
        box22.Add(self.rb_regex,   (0, 0), (1, 1), wx.EXPAND)
        box22.Add(self.tc_patt,    (0, 1), (1, 1), wx.EXPAND)
        box22.Add(self.bt_prev,    (0, 2), (1, 1), wx.EXPAND)
        box22.Add(self.bt_next,    (0, 3), (1, 1), wx.EXPAND)
        box22.Add(self.rb_replace, (1, 0), (1, 1), wx.EXPAND)
        box22.Add(self.tc_repl,    (1, 1), (1, 1), wx.EXPAND)
        box22.Add(self.bt_apply,   (1, 2), (1, 2), wx.EXPAND)
        box22.AddGrowableCol(1)

        box2 = wx.BoxSizer(wx.VERTICAL)
        flags2 = wx.EXPAND | wx.TOP | wx.RIGHT
        box2.Add(box21,       0, flags2, gap)
        box2.Add(self.tc_res, 1, flags2, gap)
        box2.Add(box22,       0, flags2, gap)
        box2.Add((0, 0),      0, flags2, gap)

        p1.SetSizer(box1)
        p2.SetSizer(box2)

        # - Initial data --------------------

        self.tc_text.Paste()
        self.tc_repl.Enable(False)
        parent.SplitVertically(p1, p2)

        # - Bind functions --------------------

        for evt, *widgets in [(stc.EVT_STC_CHANGE, self.tc_text),
                              (wx.EVT_TEXT, self.tc_patt, self.tc_repl),
                              (wx.EVT_CHECKBOX, self.cb_sorted, self.cb_unique),
                              (wx.EVT_RADIOBUTTON, self.rb_regex, self.rb_replace),
                              (wx.EVT_SET_FOCUS, self.tc_text, self.tc_patt, self.tc_repl)]:
            for widget in widgets:
                widget.Bind(evt, self.OnMatch)

        self.bt_prev.Bind(wx.EVT_BUTTON, lambda e: self.OnView(-1))
        self.bt_next.Bind(wx.EVT_BUTTON, lambda e: self.OnView( 1))

        self.bt_apply.Bind(wx.EVT_BUTTON, self.OnApply)

    def OnMatch(self, evt):
        text, patt = self.text, self.pattern
        matchs = []

        try:
            if self.rb_regex.GetValue():
                self.tc_repl.Disable()
                results = []
                for m in re.finditer(patt, patt and text, re.M):
                    results.append('\t'.join(m.groups() or [m.group()]))  # join sub-strings by '\t'
                    matchs.append(m.regs[1:] or m.regs[:1])  # match whole group if sub-groups don't exist
            else:
                self.tc_repl.Enable()
                results = re.sub(patt, self.replace, text, 0, re.M).split('\n')
            if self.cb_unique.GetValue():
                results = dict.fromkeys(results)
            if self.cb_sorted.GetValue():
                results = sorted(results)
            result = '\n'.join(results)
        except re.error as e:
            result = str(e)
        self.result = result

        self.tc_text.StartStyling(0)
        self.tc_text.SetStyling(len(text.encode()), 0)
        if len(matchs) < 10000:
            idxs = [0]
            for c in text:
                idxs.append(idxs[-1] + len(c.encode()))  # unicode index -> bytes index
            for regs in matchs:
                for p1, p2 in regs:
                    p1, p2 = idxs[p1], idxs[p2]
                    self.tc_text.StartStyling(p1)
                    self.tc_text.SetStyling(p2 - p1, 1)

        if isinstance(evt, wx.Event):
            evt.Skip()

    def OnView(self, direction):
        text, patt = self.text, self.pattern
        pos = self.tc_text.GetInsertionPoint()
        pos = len(text.encode()[:pos].decode())  # bytes index -> unicode index
        matchs = [m.span() for m in re.finditer(patt, patt and text, re.M)]
        if not matchs:
            return
        if direction > 0:
            p1, p2 = min([span for span in matchs if span[1] > pos] or [matchs[0]])
        else:
            p1, p2 = max([span for span in matchs if span[1] < pos] or [matchs[-1]])
        p1, p2 = [len(text[:p].encode()) for p in (p1, p2)]  # unicode index -> bytes index
        self.tc_text.ShowPosition(p1)
        self.tc_text.SetSelection(p1, p2)

    def OnApply(self, evt):
        self.text = self.result
        self.OnMatch(-1)


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='RegEx Matcher '+__ver__, size=(1200, 800))

        sp = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)

        self.panel = MyPanel(sp)

        sp.SetSashGravity(0.67)
        sp.SetSize(self.GetClientSize())
        sp.SetMinimumPaneSize(200)
        sp.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, lambda e: sp.SetSashGravity(sp.GetSashPosition() / sp.GetSize()[0]))

        self.Center()
        self.Show()
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)

    def OnKeyPress(self, evt):
        if wx.WXK_ESCAPE == evt.GetKeyCode():
            self.Close()
        else:
            evt.Skip()


if __name__ == '__main__':
    app = wx.App()
    MyFrame()
    app.MainLoop()
