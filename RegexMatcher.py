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


License
-------

Author:
    Shixian Li

E-mail:
    lsx7@sina.com

Website:
    https://github.com/znsoooo/regex-matcher

License:
    MIT License. Copyright (c) 2023-2025 Shixian Li (znsoooo).

"""


import os
import re
import sys
from itertools import chain

import wx
import wx.stc as stc

__version__ = 'v1.3.2'
__title__ = 'RegEx Matcher ' + __version__


def escape(text):
    table = {i: '\\' + c for i, c in zip(b'()[{?*+|^$\\.\t\n\r\v\f', '()[{?*+|^$\\.tnrvf')}
    return text.translate(table)


def mapping(idx, idxs1, idxs2):
    last_idx1, last_idx2 = 0, 0
    for idx1, idx2 in zip(idxs1, idxs2):
        if idx1 >= idx:
            return last_idx2 + (idx - last_idx1) * (idx2 - last_idx2) // max(1, idx1 - last_idx1)
        last_idx1, last_idx2 = idx1, idx2


def copy(text, info):
    do = wx.TextDataObject()
    do.SetText(text)
    if wx.TheClipboard.Open():
        wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()
        wx.MessageBox(info)


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window, callback):
        wx.FileDropTarget.__init__(self)
        window.SetDropTarget(self)
        self.callback = callback

    def OnDropFiles(self, x, y, filenames):
        self.callback(filenames[0])
        return False


class MyTextDialog(wx.TextEntryDialog):
    def __init__(self, title, prompt, text, size):
        wx.TextEntryDialog.__init__(self, None, prompt, title, text, style=wx.TE_MULTILINE | wx.OK)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.GetChildren()[1].SetFont(font)
        self.SetSize(size)
        self.Center()
        self.ShowModal()
        self.Destroy()


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

        self.OnStcChange(None)

    def GetUnicodeIndex(self, idx):
        return len(self.GetTextRaw()[:idx].decode())

    def OnKeyDown(self, evt):
        hotkey = (evt.GetModifiers(), evt.GetKeyCode())
        if hotkey == (wx.MOD_CONTROL | wx.MOD_SHIFT, wx.WXK_UP):
            self.MoveSelectedLinesUp()
        elif hotkey == (wx.MOD_CONTROL | wx.MOD_SHIFT, wx.WXK_DOWN):
            self.MoveSelectedLinesDown()
        else:
            evt.Skip()

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
        self.ShowPosition(p2)  # show the whole selection by showing p2 first
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

        # - Add widgets --------------------

        p1 = wx.Panel(sp)
        p2 = wx.Panel(sp)

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
        sp.SplitVertically(p1, p2)

        # - Bind functions --------------------

        for widget in [parent, self.tc_text, self.tc_res]:
            MyFileDropTarget(widget, self.OnOpenFile)

        self.st_text.Bind(wx.EVT_LEFT_DCLICK, lambda e: copy(self.tc_text.GetValue(), 'Text copied'))
        self.st_res .Bind(wx.EVT_LEFT_DCLICK, lambda e: copy(self.tc_res .GetValue(), 'Results copied'))

        for evt, *widgets in [
            (stc.EVT_STC_CHANGE, self.tc_text),
            (wx.EVT_TEXT, self.tc_patt, self.tc_repl),
            (wx.EVT_CHECKBOX, self.cb_sorted, self.cb_unique, self.cb_reverse),
            (wx.EVT_SET_FOCUS, self.tc_text, self.tc_patt, self.tc_repl)
        ]:
            for widget in widgets:
                widget.Bind(evt, self.OnMatch)

        self.bt_prev.Bind(wx.EVT_BUTTON, lambda e: self.OnView(-1))
        self.bt_next.Bind(wx.EVT_BUTTON, lambda e: self.OnView( 1))
        self.tc_patt.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.OnView(1 if e.GetWheelRotation() < 0 else -1))
        self.tc_repl.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.OnView(1 if e.GetWheelRotation() < 0 else -1))

        self.tc_patt.Bind(wx.EVT_KEY_DOWN, self.OnInputTextKeyDown)
        self.tc_repl.Bind(wx.EVT_KEY_DOWN, self.OnInputTextKeyDown)
        self.tc_text.Bind(wx.EVT_KEY_DOWN, self.OnStyledTextKeyDown)
        self.tc_res .Bind(wx.EVT_KEY_DOWN, self.OnStyledTextKeyDown)
        self.parent.Bind(wx.EVT_CHAR_HOOK, self.OnWindowKeyDown)

        self.tc_text.Bind(stc.EVT_STC_UPDATEUI, self.OnSelectionChanged)
        self.tc_res .Bind(stc.EVT_STC_UPDATEUI, self.OnSelectionChanged)

        self.cb_wrap.Bind(wx.EVT_CHECKBOX, self.OnWrap)
        self.bt_apply.Bind(wx.EVT_BUTTON, lambda e: self.tc_text.SetValue(self.tc_res.GetValue()))

    def OnStyledTextKeyDown(self, evt):
        hotkey = (evt.GetModifiers(), evt.GetKeyCode())
        if hotkey == (wx.MOD_CONTROL, ord('F')):
            selected = evt.GetEventObject().GetSelectedText()
            pattern = escape(selected)
            self.tc_patt.SetValue(pattern)
            self.tc_patt.SetFocus()
            self.tc_patt.SelectAll()
        evt.Skip()

    def OnInputTextKeyDown(self, evt):
        key = evt.GetKeyCode()
        if key in [wx.WXK_UP, wx.WXK_PAGEUP]:
            self.OnView(-1)
        elif key in [wx.WXK_DOWN, wx.WXK_PAGEDOWN]:
            self.OnView(1)
        elif key == wx.WXK_RETURN:
            self.tc_text.SetValue(self.tc_res.GetValue())
        elif evt.ControlDown() and key == ord('G') and self.tc_patt.HasFocus() and self.tc_patt.GetStringSelection():
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

    def OnWindowKeyDown(self, evt):
        hotkey = (evt.GetModifiers(), evt.GetKeyCode())
        if hotkey == (wx.MOD_CONTROL, ord('O')):
            self.OnOpenFile()
        elif hotkey == (wx.MOD_CONTROL, ord('S')):
            self.OnSaveFile()
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
        patt = self.tc_patt.GetValue() or '$0'  # non-empty pattern or an impossible pattern
        repl = self.tc_repl.GetValue()
        finds = self.finds = []
        repls = self.repls = []

        try:
            finds[:] = [m.span() for m in re.finditer(patt, text, re.M)]
            if self.mode == 'regex':
                results = []
                offset = 0
                for m in re.findall(patt, text, re.M):
                    results.append(m if isinstance(m, str) else '\t'.join(m))  # join sub-strings by '\t'
                    length = len(results[-1])
                    repls.append((offset, offset + length))
                    offset += length + 1
            else:
                # fix `re.sub` bug in PY36: https://bugs.python.org/issue32308
                strings, idx = [], 0
                for m in re.finditer(patt, text, re.M):
                    repls.append(m.expand(repl).replace('\0', m.group()))  # replace "\0" as group 0
                    strings += [text[idx:m.start()], repls[-1]]
                    idx = m.end()
                strings.append(text[idx:])

                results = ''.join(strings).split('\n')
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
        pos = self.tc_text.GetUnicodeIndex(pos)
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

    def OnSelectionChanged(self, evt):
        if self.cb_unique.GetValue() or self.cb_sorted.GetValue() or self.cb_reverse.GetValue():
            return
        obj = evt.GetEventObject()
        if not obj.HasFocus():
            return
        p11, p12 = obj.GetSelection()
        p11 = obj.GetUnicodeIndex(p11)
        p12 = obj.GetUnicodeIndex(p12)
        finds_idxs = list(chain.from_iterable(self.finds)) + [len(self.tc_text.GetValue())]  # speed up
        repls_idxs = list(chain.from_iterable(self.repls)) + [len(self.tc_res.GetValue())]
        if obj is self.tc_text:
            p21 = mapping(p11, finds_idxs, repls_idxs)
            p22 = mapping(p12, finds_idxs, repls_idxs)
            self.tc_res.SetUnicodeSelection(p21, p22)
        if obj is self.tc_res:
            p21 = mapping(p11, repls_idxs, finds_idxs)
            p22 = mapping(p12, repls_idxs, finds_idxs)
            self.tc_text.SetUnicodeSelection(p21, p22)

    def OnWrap(self, evt):
        wrap_mode = stc.STC_WRAP_CHAR if self.cb_wrap.GetValue() else stc.STC_WRAP_NONE
        self.tc_text.SetWrapMode(wrap_mode)
        self.tc_res.SetWrapMode(wrap_mode)

    def OnOpenFile(self, path=None):
        if not path:
            dlg = wx.FileDialog(None, 'Open file',
                wildcard='Text file|*.txt|All file|*.*',
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
        if path:
            for encoding in ['u8', 'u16', 'gbk', None]:
                try:
                    with open(path, encoding=encoding) as f:
                        return self.tc_text.SetValue(f.read())
                except UnicodeError:
                    pass

    def OnSaveFile(self):
        dlg = wx.FileDialog(None, 'Save file',
            defaultFile='result',
            wildcard='Text file|*.txt|All file|*.*',
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            with open(dlg.GetPath(), 'w', encoding='u8') as f:
                f.write(self.tc_res.GetValue())

    def SetSummary(self, total=0, current=0):
        patt = self.tc_patt.GetValue()
        title = patt.strip() + ' - ' + __title__ if patt else __title__
        self.parent.SetTitle(title)
        summary = '' if patt == '' else f'{total}' if current == 0 else f'{current}/{total}'
        self.st_res.SetLabel('Results: ' + summary)


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=(1200, 800))

        self.history = os.path.splitext(sys.argv[0])[0] + '.log'

        sp = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)

        self.panel = MyPanel(self, sp)

        sp.SetSashGravity(0.67)
        sp.SetSize(self.GetClientSize())
        sp.SetMinimumPaneSize(20)
        sp.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, lambda e: sp.SetSashGravity(sp.GetSashPosition() / sp.GetSize()[0]))

        icon_path = os.path.realpath(__file__ + '/../icon.ico')
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
            text = re.__doc__.strip() + '\n'
            MyTextDialog('Regex Syntax', 'Help on module re:', text, (800, 600))
        elif key == wx.WXK_F12:
            text = __doc__[__doc__.find('License'):].strip() + '\n'
            MyTextDialog('About Regex-Matcher', 'License:', text, (600, 400))
        else:
            evt.Skip()

    def OnOpen(self):
        pnl = self.panel
        try:
            with open(self.history, 'r', encoding='u8') as f:
                log = f.read()
            mask, patt, repl, text = log.split('\n', 3)
            for i, cb in enumerate([pnl.cb_wrap, pnl.cb_sorted, pnl.cb_unique, pnl.cb_reverse]):
                cb.SetValue(int(mask[i]))
            pnl.OnWrap(-1)
            pnl.mode = ['regex', 'replace'][int(mask[4])]
        except Exception:
            patt, repl, text = r'apple', '', __doc__.lstrip()
        pnl.tc_patt.SetValue(patt)
        pnl.tc_repl.SetValue(repl)
        pnl.tc_text.SetValue(text)

    def OnClose(self, evt):
        pnl = self.panel
        mask = '%d%d%d%d%d' % (pnl.cb_wrap.Value, pnl.cb_sorted.Value, pnl.cb_unique.Value, pnl.cb_reverse.Value, ['regex', 'replace'].index(pnl.mode))
        log = '\n'.join([mask, pnl.tc_patt.Value, pnl.tc_repl.Value, pnl.tc_text.Value])
        with open(self.history, 'w', encoding='u8') as f:
            f.write(log)
        evt.Skip()


if __name__ == '__main__':
    app = wx.App()
    MyFrame()
    app.MainLoop()
