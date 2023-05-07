import os
import re
import time

import wx
import wx.stc as stc

__ver__ = 'v0.2.3'


def ReadFile(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.docx':
        pass
    else:
        try:
            with open(path, 'r', encoding='u8') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, 'r') as f:
                text = f.read()
    return text


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


class MyPanel(wx.Panel, Private):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # - Add widgets --------------------

        self.tc_text = MyTextCtrl(self)
        self.tc_res  = MyTextCtrl(self)
        self.tc_patt = wx.TextCtrl(self, size=(20, -1))
        self.tc_repl = wx.TextCtrl(self, size=(20, -1))

        self.cb_sorted  = wx.CheckBox(self, -1, 'Sorted')
        self.cb_unique  = wx.CheckBox(self, -1, 'Unique')
        self.rb_regex   = wx.RadioButton(self, -1, 'RegEx:', style=wx.RB_GROUP)
        self.rb_replace = wx.RadioButton(self, -1, 'Replace:')

        bt_open  = wx.Button(self, -1, 'Open',  size=(48, 24))
        bt_save  = wx.Button(self, -1, 'Save',  size=(48, 24))
        bt_prev  = wx.Button(self, -1, '<',     size=(24, 24))
        bt_next  = wx.Button(self, -1, '>',     size=(24, 24))
        bt_apply = wx.Button(self, -1, 'Apply', size=(24, 24))

        TEXT = lambda s: wx.StaticText(self, -1, s)

        # - Set layout --------------------

        flags = wx.EXPAND

        box1 = wx.BoxSizer()
        box1.Add(TEXT('Text:'), 1, wx.ALIGN_CENTER)
        box1.Add(bt_open, 0, wx.LEFT, 5)
        box1.Add(bt_save, 0, wx.LEFT, 5)

        box2 = wx.BoxSizer()
        box2.Add(TEXT('Result:'), 1, wx.ALIGN_CENTER)
        box2.Add(self.cb_sorted,  0, wx.ALIGN_CENTER)
        box2.Add(self.cb_unique,  0, wx.ALIGN_CENTER)

        box3 = wx.GridBagSizer(vgap=5, hgap=5)
        box3.Add(self.rb_regex,   (0, 0), (1, 1), flags)
        box3.Add(self.tc_patt,    (0, 1), (1, 1), flags)
        box3.Add(bt_prev,         (0, 2), (1, 1), flags)
        box3.Add(bt_next,         (0, 3), (1, 1), flags)
        box3.Add(self.rb_replace, (1, 0), (1, 1), flags)
        box3.Add(self.tc_repl,    (1, 1), (1, 1), flags)
        box3.Add(bt_apply,        (1, 2), (1, 2), flags)
        box3.AddGrowableCol(1)

        box4 = wx.GridBagSizer(vgap=5, hgap=5)
        box4.Add(box1,         (0, 0), (1, 1), flags)
        box4.Add(box2,         (0, 1), (1, 1), flags)
        box4.Add(self.tc_text, (1, 0), (2, 1), flags)
        box4.Add(self.tc_res,  (1, 1), (1, 1), flags)
        box4.Add(box3,         (2, 1), (1, 1), flags)
        box4.AddGrowableRow(1)
        box4.AddGrowableCol(0, 2)
        box4.AddGrowableCol(1, 1)

        box = wx.BoxSizer()
        box.Add(box4, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(box)

        # - Initial data --------------------

        self.tc_patt.SetValue('')
        self.tc_repl.Enable(False)

        # - Bind functions --------------------

        bt_open.Bind(wx.EVT_BUTTON, self.OnOpen)
        bt_save.Bind(wx.EVT_BUTTON, self.OnSave)

        for evt, *widgets in [(stc.EVT_STC_CHANGE, self.tc_text),
                              (wx.EVT_TEXT, self.tc_patt, self.tc_repl),
                              (wx.EVT_CHECKBOX, self.cb_sorted, self.cb_unique),
                              (wx.EVT_RADIOBUTTON, self.rb_regex, self.rb_replace),
                              (wx.EVT_SET_FOCUS, self.tc_text, self.tc_patt, self.tc_repl)]:
            for widget in widgets:
                widget.Bind(evt, self.OnMatch)

        bt_prev.Bind(wx.EVT_BUTTON, lambda e: self.OnView(-1))
        bt_next.Bind(wx.EVT_BUTTON, lambda e: self.OnView( 1))

        bt_apply.Bind(wx.EVT_BUTTON, self.OnApply)

    def OnOpen(self, evt):
        dlg = wx.FileDialog(self, wildcard='Text file|*.txt|All file|*.*',
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                self.text += ReadFile(path) + '\n'
            self.tc_text.SetFocus()
            wx.CallAfter(self.tc_text.GotoLine, self.tc_text.GetLineCount())
        dlg.Destroy()

    def OnSave(self, evt):
        dlg = wx.FileDialog(self, wildcard='Text file|*.txt', defaultFile=time.strftime('TXT_%Y%m%d_%H%M%S.txt'),
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w', encoding='u8') as f:
                f.write(self.text)
        dlg.Destroy()

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

        self.panel = MyPanel(self)
        self.panel.SetSize(self.GetClientSize())
        self.log = 'log.txt'

        self.OnOpen()
        self.Center()
        self.Show()

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnKeyPress(self, evt):
        if wx.WXK_ESCAPE == evt.GetKeyCode():
            self.Close()
        else:
            evt.Skip()

    def OnOpen(self):
        if os.path.isfile(self.log):
            self.panel.text = ReadFile(self.log)

    def OnClose(self, evt):
        text = self.panel.text
        if text:
            with open(self.log, 'w', encoding='u8') as f:
                f.write(text)
        elif os.path.isfile(self.log):
            os.remove(self.log)
        evt.Skip()


if __name__ == '__main__':
    app = wx.App()
    MyFrame()
    app.MainLoop()
