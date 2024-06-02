r"""
Regex Matcher
=============

Input original text on left window, output text shows on the right.
Input RegEx text, output the matching results.
Input Replace pattern, output the replacement text.
The matching or replacement positions are highlighted on the both sides of window.
Press Up / Down to select the matching positions synchronously.


Text for Test
-------------

[Apple apple pineapple]

+---------------+--------------------------+
| RegEx         | Match Rule               |
+---------------+--------------------------+
| apple         | Match case               |
| (?i)apple     | Ignore case              |
| \bapple\b     | Match word & match case  |
| (?i)\bapple\b | Match word & ignore case |
+---------------+--------------------------+

* Press F1 for detail help.


Licence
-------

Author:
    Shixian Li

E-mail:
    lsx7@sina.com

Website:
    https://github.com/znsoooo/regex-matcher

Licence:
    MIT License. Copyright (c) 2023-2024 Shixian Li (znsoooo).

"""


import os
import re
import sys

import wx
import wx.stc as stc

__version__ = 'v1.2.0'
__title__ = 'RegEx Matcher ' + __version__


def escape(text):
    table = {i: '\\' + c for i, c in zip(b'()[{?*+|^$\\.\t\n\r\v\f', '()[{?*+|^$\\.tnrvf')}
    return text.translate(table)


def help():
    dlg = wx.TextEntryDialog(None, 'Help on module re:', 'Syntax Help', re.__doc__.strip(), style=wx.TE_MULTILINE|wx.OK)
    dlg.SetSize(800, 600)
    dlg.Center()
    dlg.ShowModal()
    dlg.Destroy()


def copy(text, info):
    do = wx.TextDataObject()
    do.SetText(text)
    if wx.TheClipboard.Open():
        wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()
        wx.MessageBox(info)


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

        self.Bind(stc.EVT_STC_CHANGE, self.OnStcChange)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        self.OnStcChange(-1)

    def OnKeyDown(self, evt):
        evt.Skip()
        if evt.ControlDown() and evt.ShiftDown():
            if evt.GetKeyCode() == wx.WXK_UP:
                self.MoveSelectedLinesUp()
            elif evt.GetKeyCode() == wx.WXK_DOWN:
                self.MoveSelectedLinesDown()

    def OnStcChange(self, evt):
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

        self.cb_wrap = wx.CheckBox(p1, -1, 'Wrap')
        self.cb_wrap.SetValue(True)
        self.cb_sorted = wx.CheckBox(p2, -1, 'Sorted')
        self.cb_unique = wx.CheckBox(p2, -1, 'Unique')
        self.cb_reverse = wx.CheckBox(p2, -1, 'Reverse')

        self.tc_patt = wx.TextCtrl(p2, size=(20, -1), style=wx.TE_PROCESS_ENTER)
        self.tc_repl = wx.TextCtrl(p2, size=(20, -1), style=wx.TE_PROCESS_ENTER)

        self.bt_prev  = wx.Button(p2, -1, '<',     size=(24, 24))
        self.bt_next  = wx.Button(p2, -1, '>',     size=(24, 24))
        self.bt_apply = wx.Button(p2, -1, 'Apply', size=(24, 24))

        self.st_text = wx.StaticText(p1, -1, 'Text:')
        self.st_res  = wx.StaticText(p2, -1, 'Results:')
        self.st_patt = wx.StaticText(p2, -1, 'RegEx:')
        self.st_repl = wx.StaticText(p2, -1, 'Replace:')

        # - Set layout --------------------

        gap = sp.GetSashSize()

        box11 = wx.BoxSizer()
        box11.Add(self.st_text, 1, wx.ALIGN_CENTER)
        box11.Add(self.cb_wrap, 0, wx.ALIGN_CENTER)

        box1 = wx.BoxSizer(wx.VERTICAL)
        flags1 = wx.EXPAND | wx.TOP | wx.LEFT
        box1.Add(box11,        0, flags1, gap)
        box1.Add(self.tc_text, 1, flags1, gap)
        box1.Add((0, 0),       0, flags1, gap)

        box21 = wx.BoxSizer()
        box21.Add(self.st_res,     1, wx.ALIGN_CENTER)
        box21.Add(self.cb_sorted,  0, wx.ALIGN_CENTER)
        box21.Add(self.cb_unique,  0, wx.ALIGN_CENTER)
        box21.Add(self.cb_reverse, 0, wx.ALIGN_CENTER)

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

        sp.SplitVertically(p1, p2)

        # - Bind functions --------------------

        self.st_text.Bind(wx.EVT_LEFT_DCLICK, lambda e: copy(self.tc_text.GetValue(), 'Text copied.'))
        self.st_res .Bind(wx.EVT_LEFT_DCLICK, lambda e: copy(self.tc_res .GetValue(), 'Results copied.'))

        for evt, *widgets in [(stc.EVT_STC_CHANGE, self.tc_text),
                              (wx.EVT_TEXT, self.tc_patt, self.tc_repl),
                              (wx.EVT_CHECKBOX, self.cb_sorted, self.cb_unique, self.cb_reverse),
                              (wx.EVT_SET_FOCUS, self.tc_text, self.tc_patt, self.tc_repl)]:
            for widget in widgets:
                widget.Bind(evt, self.OnMatch)

        self.bt_prev.Bind(wx.EVT_BUTTON, lambda e: self.OnView(-1))
        self.bt_next.Bind(wx.EVT_BUTTON, lambda e: self.OnView( 1))
        self.tc_patt.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.OnView(1 if e.GetWheelRotation() < 0 else -1))
        self.tc_repl.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.OnView(1 if e.GetWheelRotation() < 0 else -1))
        self.tc_patt.Bind(wx.EVT_KEY_DOWN, self.OnText34KeyDown)
        self.tc_repl.Bind(wx.EVT_KEY_DOWN, self.OnText34KeyDown)

        self.tc_text.Bind(wx.EVT_KEY_DOWN, self.OnText12KeyDown)
        self.tc_res .Bind(wx.EVT_KEY_DOWN, self.OnText12KeyDown)

        self.cb_wrap.Bind(wx.EVT_CHECKBOX, self.OnWrap)
        self.bt_apply.Bind(wx.EVT_BUTTON, lambda e: self.tc_text.SetValue(self.tc_res.GetValue()))

    def OnText12KeyDown(self, evt):
        if wx.MOD_CONTROL == evt.GetModifiers() and ord('F') == evt.GetKeyCode():
            selected = evt.GetEventObject().GetSelectedText()
            pattern = escape(selected)
            self.tc_patt.SetValue(pattern)
            self.tc_patt.SetFocus()
            self.tc_patt.SelectAll()
        evt.Skip()

    def OnText34KeyDown(self, evt):
        code = evt.GetKeyCode()
        if code in [wx.WXK_UP, wx.WXK_PAGEUP]:
            self.OnView(-1)
        elif code in [wx.WXK_DOWN, wx.WXK_PAGEDOWN]:
            self.OnView(1)
        elif code == wx.WXK_RETURN:
            self.tc_text.SetValue(self.tc_res.GetValue())
        elif evt.ControlDown() and code == ord('G') and self.tc_patt.HasFocus() and self.tc_patt.GetStringSelection():
            text = self.tc_patt.GetValue()
            p1, p2 = self.tc_patt.GetSelection()
            if not evt.ShiftDown():
                self.tc_patt.SetValue(text[:p1] + '(' + text[p1:p2] + ')' + text[p2:])
                self.tc_patt.SetSelection(p1, p2 + 2)
            elif text[p1] == '(' and text[p2-1] == ')':
                self.tc_patt.SetValue(text[:p1] + text[p1+1:p2-1] + text[p2:])
                self.tc_patt.SetSelection(p1, p2 - 2)
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
        finds = self.finds = []
        repls = self.repls = []
        try:
            finds += [m.span() for m in re.finditer(patt, text, re.M)]
            if self.mode == 'regex':
                results = []
                offset = 0
                for m in re.findall(patt, text, re.M):
                    results.append(m if isinstance(m, str) else '\t'.join(m))  # join sub-strings by '\t'
                    length = len(results[-1])
                    repls.append((offset, offset + length))
                    offset += length + 1
            else:
                callback = lambda m: repls.append(m.expand(repl).replace('\0', m.group())) or repls[-1]  # replace "\0" as group 0
                results = re.sub(patt, callback, text, 0, re.M).split('\n')
                offset = 0
                for i, ((p1, p2), repl) in enumerate(zip(finds, repls)):
                    diff = len(repl) - (p2 - p1)
                    repls[i] = (p1 + offset, p2 + offset + diff)
                    offset += diff
            if self.cb_unique.GetValue():
                results = list(dict.fromkeys(results))
            if self.cb_sorted.GetValue():
                results = sorted(results)
            if self.cb_reverse.GetValue():
                results = reversed(results)
            result = '\n'.join(results)
        except re.error as e:
            result = str(e)
        self.tc_res.SetValue(result)

        self.SetSummary(len(finds))
        self.tc_text.SetUnicodeHighlights(finds)
        if self.cb_unique.GetValue() or self.cb_sorted.GetValue() or self.cb_reverse.GetValue():
            repls.clear()
        self.tc_res.SetUnicodeHighlights(repls)

    def OnView(self, direction):
        finds, repls = self.finds, self.repls
        pos = self.tc_text.GetInsertionPoint()
        pos = len(self.tc_text.GetValue().encode()[:pos].decode())  # bytes index -> unicode index
        if finds:
            if direction > 0:
                p1, p2 = min([span for span in finds if span[1] > pos] or [finds[0]])
            else:
                p1, p2 = max([span for span in finds if span[1] < pos] or [finds[-1]])
            self.tc_text.SetUnicodeSelection(p1, p2)
            index = finds.index((p1, p2))
            self.SetSummary(len(finds), index + 1)
            if repls:
                p1, p2 = repls[index]
                self.tc_res.SetUnicodeSelection(p1, p2)

    def OnWrap(self, evt):
        wrap_mode = stc.STC_WRAP_CHAR if evt.GetSelection() else stc.STC_WRAP_NONE
        self.tc_text.SetWrapMode(wrap_mode)
        self.tc_res.SetWrapMode(wrap_mode)

    def SetSummary(self, total=0, current=0):
        patt = self.tc_patt.GetValue()
        title = patt.strip() + ' - ' + __title__ if patt else __title__
        self.parent.SetTitle(title)
        summary = '' if patt == '' else f'{total}' if current == 0 else f'{current}/{total}'
        self.st_res.SetLabel('Results: ' + summary)


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=(1200, 800))

        self.history = os.path.realpath(sys.argv[0] + '/../history.txt')

        sp = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)

        self.panel = MyPanel(self, sp)

        sp.SetSashGravity(0.67)
        sp.SetSize(self.GetClientSize())
        sp.SetMinimumPaneSize(20)
        sp.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, lambda e: sp.SetSashGravity(sp.GetSashPosition() / sp.GetSize()[0]))

        icon_path = os.path.realpath(__file__ + '/../icon.png')
        if os.path.isfile(icon_path):
            self.SetIcons(wx.IconBundle(icon_path))

        self.OnOpen()
        self.Center()
        self.Show()

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnKeyPress(self, evt):
        key = evt.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            self.Close()
        elif key == wx.WXK_F1:
            help()
        else:
            evt.Skip()

    def OnOpen(self):
        try:
            with open(self.history, 'r', encoding='u8') as f:
                log = f.read()
            patt, repl, text = log.split('\n', 2)
        except Exception:
            patt, repl, text = r'apple', '', __doc__.lstrip()
        self.panel.tc_patt.SetValue(patt)
        self.panel.tc_repl.SetValue(repl)
        self.panel.tc_text.SetValue(text)

    def OnClose(self, evt):
        pnl = self.panel
        log = '\n'.join(tc.GetValue() for tc in (pnl.tc_patt, pnl.tc_repl, pnl.tc_text))
        with open(self.history, 'w', encoding='u8') as f:
            f.write(log)
        evt.Skip()


if __name__ == '__main__':
    app = wx.App()
    MyFrame()
    app.MainLoop()
