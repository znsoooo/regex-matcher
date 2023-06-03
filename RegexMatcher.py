import re

import wx
import wx.stc as stc

__ver__ = 'v1.0.0'


class MyTextCtrl(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'face:Courier New,size:11')
        self.StyleSetSpec(1, 'back:#FFFF00')
        self.StyleSetSpec(2, 'back:#00FFFF')

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

    def SetUnicodeHighlights(self, spans):
        text = self.GetValue()
        self.StartStyling(0)
        self.SetStyling(len(text.encode()), 0)
        if spans and len(spans) < 10000:
            idxs = [0]
            for c in text:
                idxs.append(idxs[-1] + len(c.encode()))  # unicode index -> bytes index
            for i, (p1, p2) in enumerate(spans):
                p1, p2 = idxs[p1], idxs[p2]
                self.StartStyling(p1)
                self.SetStyling(p2 - p1, (i % 2) + 1)

    def SetUnicodeSelection(self, p1, p2):
        text = self.GetValue()
        p1, p2 = (len(text[:p].encode()) for p in (p1, p2))  # unicode index -> bytes index
        self.ShowPosition(p1)
        self.SetSelection(p1, p2)

    def StartStyling(self, start):
        try:
            super().StartStyling(start)
        except TypeError:  # compatible for old version of wxPython
            super().StartStyling(start, 0xFFFF)


class MyPanel:
    def __init__(self, parent, sp):
        self.parent = parent

        self.mode = 'regex'

        p1 = wx.Panel(sp)
        p2 = wx.Panel(sp)

        # - Add widgets --------------------

        self.tc_text = MyTextCtrl(p1)
        self.tc_res  = MyTextCtrl(p2)

        self.cb_sorted = wx.CheckBox(p2, -1, 'Sorted')
        self.cb_unique = wx.CheckBox(p2, -1, 'Unique')

        self.tc_patt = wx.TextCtrl(p2, size=(20, -1))
        self.tc_repl = wx.TextCtrl(p2, size=(20, -1))

        self.bt_prev  = wx.Button(p2, -1, '<',     size=(24, 24))
        self.bt_next  = wx.Button(p2, -1, '>',     size=(24, 24))
        self.bt_apply = wx.Button(p2, -1, 'Apply', size=(24, 24))

        self.st_text = wx.StaticText(p1, -1, 'Text:')
        self.st_res  = wx.StaticText(p2, -1, 'Result:')
        self.st_patt = wx.StaticText(p2, -1, 'RegEx:')
        self.st_repl = wx.StaticText(p2, -1, 'Replace:')

        # - Set layout --------------------

        gap = sp.GetSashSize()

        box1 = wx.BoxSizer(wx.VERTICAL)
        flags1 = wx.EXPAND | wx.TOP | wx.LEFT
        box1.Add(self.st_text, 0, flags1, gap)
        box1.Add(self.tc_text, 1, flags1, gap)
        box1.Add((0, 0),       0, flags1, gap)

        box21 = wx.BoxSizer()
        box21.Add(self.st_res,    1, wx.ALIGN_CENTER)
        box21.Add(self.cb_sorted, 0, wx.ALIGN_CENTER)
        box21.Add(self.cb_unique, 0, wx.ALIGN_CENTER)

        box22 = wx.GridBagSizer(vgap=gap, hgap=gap)
        box22.Add(self.st_patt,  (0, 0), (1, 1), wx.ALIGN_CENTRE_VERTICAL)
        box22.Add(self.tc_patt,  (0, 1), (1, 1), wx.EXPAND)
        box22.Add(self.bt_prev,  (0, 2), (1, 1), wx.EXPAND)
        box22.Add(self.bt_next,  (0, 3), (1, 1), wx.EXPAND)
        box22.Add(self.st_repl,  (1, 0), (1, 1), wx.ALIGN_CENTRE_VERTICAL)
        box22.Add(self.tc_repl,  (1, 1), (1, 1), wx.EXPAND)
        box22.Add(self.bt_apply, (1, 2), (1, 2), wx.EXPAND)
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
        sp.SplitVertically(p1, p2)

        # - Bind functions --------------------

        for evt, *widgets in [(stc.EVT_STC_CHANGE, self.tc_text),
                              (wx.EVT_TEXT, self.tc_patt, self.tc_repl),
                              (wx.EVT_CHECKBOX, self.cb_sorted, self.cb_unique),
                              (wx.EVT_SET_FOCUS, self.tc_text, self.tc_patt, self.tc_repl)]:
            for widget in widgets:
                widget.Bind(evt, self.OnMatch)

        self.bt_prev.Bind(wx.EVT_BUTTON, lambda e: self.OnView(-1))
        self.bt_next.Bind(wx.EVT_BUTTON, lambda e: self.OnView( 1))
        self.tc_patt.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.OnView(1 if e.GetWheelRotation() < 0 else -1))
        self.tc_repl.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.OnView(1 if e.GetWheelRotation() < 0 else -1))
        self.tc_patt.Bind(wx.EVT_CHAR, self.OnKeyDown)
        self.tc_repl.Bind(wx.EVT_CHAR, self.OnKeyDown)

        self.bt_apply.Bind(wx.EVT_BUTTON, lambda e: self.tc_text.SetValue(self.tc_res.GetValue()))

    def OnKeyDown(self, evt):
        code = evt.GetKeyCode()
        if code in (wx.WXK_UP, wx.WXK_PAGEUP):
            self.OnView(-1)
        elif code in (wx.WXK_DOWN, wx.WXK_PAGEDOWN):
            self.OnView(1)
        else:
            evt.Skip()

    def OnMatch(self, evt):
        if isinstance(evt, wx.Event):
            evt.Skip()

        if self.tc_patt.HasFocus():
            self.mode = 'regex'
        elif self.tc_repl.HasFocus():
            self.mode = 'replace'

        text = self.tc_text.GetValue()
        patt = self.tc_patt.GetValue() or '(?=A)(?=Z)'  # non-empty pattern or an impossible pattern
        repl = self.tc_repl.GetValue()
        finds, repls = [], []
        try:
            finds = [m.span() for m in re.finditer(patt, text, re.M)]
            if self.mode == 'regex':
                results = []
                offset = 0
                for m in re.findall(patt, text, re.M):
                    results.append(m if isinstance(m, str) else '\t'.join(m))  # join sub-strings by '\t'
                    length = len(results[-1])
                    repls.append((offset, offset + length))
                    offset += length + 1
            else:
                results = re.sub(patt, lambda m: repls.append(m.expand(repl)) or repls[-1], text, 0, re.M).split('\n')
                offset = 0
                for i, ((p1, p2), repl) in enumerate(zip(finds, repls)):
                    diff = len(repl) - (p2 - p1)
                    repls[i] = (p1 + offset, p2 + offset + diff)
                    offset += diff
            if self.cb_unique.GetValue():
                results = dict.fromkeys(results)
            if self.cb_sorted.GetValue():
                results = sorted(results)
            result = '\n'.join(results)
        except re.error as e:
            result = str(e)
        self.tc_res.SetValue(result)

        self.SetTitle(len(finds))
        self.tc_text.SetUnicodeHighlights(finds)
        if self.cb_unique.GetValue() or self.cb_sorted.GetValue():
            repls.clear()
        self.tc_res.SetUnicodeHighlights(repls)

        return finds, repls

    def OnView(self, direction):
        finds, repls = self.OnMatch(-1)
        pos = self.tc_text.GetInsertionPoint()
        pos = len(self.tc_text.GetValue().encode()[:pos].decode())  # bytes index -> unicode index
        if finds:
            if direction > 0:
                p1, p2 = min([span for span in finds if span[1] > pos] or [finds[0]])
            else:
                p1, p2 = max([span for span in finds if span[1] < pos] or [finds[-1]])
            self.tc_text.SetUnicodeSelection(p1, p2)
            index = finds.index((p1, p2))
            self.SetTitle(len(finds), index + 1)
            if repls:
                p1, p2 = repls[index]
                self.tc_res.SetUnicodeSelection(p1, p2)

    def SetTitle(self, total=0, idx=0):
        if not total:
            info = ''
        elif not idx:
            info = '%d - ' % total
        else:
            info = '%d/%d - ' % (idx, total)
        self.parent.SetTitle(info + 'RegEx Matcher ' + __ver__)


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=(1200, 800))

        sp = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)

        self.panel = MyPanel(self, sp)

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
