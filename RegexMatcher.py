import re
import wx

__ver__ = 'v0.1.0'


class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.text    = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.result  = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.pattern = wx.TextCtrl(self, size=(20, -1))

        btn_up = wx.Button(self, -1, '<', size=(24, 24))
        btn_dn = wx.Button(self, -1, '>', size=(24, 24))

        gbs = wx.GridBagSizer(vgap=5, hgap=5)

        TEXT = lambda s: wx.StaticText(self, -1, s)
        gbs.Add(TEXT('Text:'),   (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbs.Add(TEXT('Result:'), (0, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gbs.Add(self.text,       (1, 0), (2, 1), flag=wx.EXPAND)
        gbs.Add(self.result,     (1, 1), (1, 4), flag=wx.EXPAND)
        gbs.Add(TEXT('RegEx:'),  (2, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gbs.Add(self.pattern,    (2, 2), flag=wx.EXPAND)
        gbs.Add(btn_up,          (2, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        gbs.Add(btn_dn,          (2, 4), flag=wx.ALIGN_CENTER_VERTICAL)

        gbs.AddGrowableRow(1)
        gbs.AddGrowableCol(0, 2)
        gbs.AddGrowableCol(2, 1)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(box)

        self.text   .Bind(wx.EVT_TEXT, self.OnMatch)
        self.pattern.Bind(wx.EVT_TEXT, self.OnMatch)
        btn_up.Bind(wx.EVT_BUTTON, lambda e: self.OnView(-1))
        btn_dn.Bind(wx.EVT_BUTTON, lambda e: self.OnView( 1))

    def OnMatch(self, evt):
        try:
            patt = self.pattern.GetValue()
            results = re.findall(patt, patt and self.text.GetValue(), re.M)
            result = '\n'.join(results)
        except re.error as e:
            result = str(e)
        self.result.SetValue(result)

    def OnView(self, direction):
        pos = self.text.GetInsertionPoint()
        matchs = list(re.finditer(self.pattern.GetValue(), self.text.GetValue(), re.M))
        if direction > 0:
            p1, p2 = matchs[0].span()
            for m in matchs:
                if m.start() > pos:
                    p1, p2 = m.span()
                    break
        else:
            p1, p2 = matchs[-1].span()
            for m in reversed(matchs):
                if m.start() < pos:
                    p1, p2 = m.span()
                    break
        self.text.SetSelection(p1, p2)
        self.text.ShowPosition(p1)
        self.text.SetFocus()


if __name__ == '__main__':
    app = wx.App()
    frm = wx.Frame(None, title='RegEx Matcher '+__ver__, size=(1200, 800))
    pnl = MyPanel(frm)
    frm.Centre()
    frm.Show()
    app.MainLoop()
