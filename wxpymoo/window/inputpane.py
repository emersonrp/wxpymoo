import wx
import wx.richtext
import wxpymoo.prefs as prefs

class InputPane(wx.richtext.RichTextCtrl):

    def __init__(self, connection):
        self.parent = connection.splitter
        wx.richtext.RichTextCtrl.__init__(self, self.parent,
            style = wx.TE_PROCESS_ENTER | wx.TE_MULTILINE
        )

        self.connection = connection
        self.cmd_history = CommandHistory()

        self.Bind(wx.EVT_TEXT_ENTER, self.send_to_connection )
        self.Bind(wx.EVT_TEXT,       self.update_command_history )
        self.Bind(wx.EVT_KEY_DOWN,   self.check_for_interesting_keystrokes )
##       EVT_CHAR      ( self,     \&debug_key_code )

        if (prefs.get('use_x_copy_paste') == 'True'):
            self.Bind(wx.EVT_MIDDLE_UP                  , self.paste_from_selection )
            self.Bind(wx.EVT_RICHTEXT_SELECTION_CHANGED , self.copy_from_selection )

        self.Clear()
        self.restyle_thyself()

    def paste_from_selection(self):
        # we only get here if we have .prefs.use_x_copy paste set.
        # We might have selected that option in a non-Unix context, though,
        # so we want to check to decide which clipboard to paste from.
        #if WxMOO.Utility.is_unix(): wxTheClipboard.UsePrimarySelection(True)
        self.Paste()
        #if WxMOO.Utility.is_unix(): wxTheClipboard.UsePrimarySelection(False)

    def copy_from_selection(self):
        #if WxMOO.Utility.is_unix(): wxTheClipboard.UsePrimarySelection(True)
        self.Copy()
        #if WxMOO.Utility.is_unix(): wxTheClipboard.UsePrimarySelection(False)

    def restyle_thyself(self):
        basic_style = wx.richtext.RichTextAttr()
        basic_style.SetTextColour      (prefs.get('input_fgcolour'))
        basic_style.SetBackgroundColour(prefs.get('input_bgcolour'))

        self.SetBackgroundColour(prefs.get('input_bgcolour'))
        self.SetBasicStyle(basic_style)

        font = wx.NullFont
        font.SetNativeFontInfoFromString(prefs.get('input_font'))
        self.SetFont(font)

    ### HANDLERS
    def send_to_connection(self, evt):
        if self.connection:
            stuff = self.GetValue()  #    =~ s/\n//g
            self.cmd_history.add(stuff)
            self.connection.output(stuff)
            self.Clear()

    def update_command_history(self, evt):
        self.cmd_history.update(self.GetValue())

    def debug_key_code(self, evt):
        k = evt.GetKeyCode()
        # say STDERR "EVT_CHAR k"

    def check_for_interesting_keystrokes(self, evt):
        k = evt.GetKeyCode()

        if   k == wx.WXK_UP:       self.SetValue(self.cmd_history.prev())
        elif k == wx.WXK_DOWN:     self.SetValue(self.cmd_history.next())
        elif k == wx.WXK_PAGEUP:   self.connection.output_pane.ScrollPages(-1)
        elif k == wx.WXK_PAGEDOWN: self.connection.output_pane.ScrollPages(1)
        elif k == wx.WXK_INSERT:
            if evt.ShiftDown: self.Paste
        elif k == 23:  # Ctrl-W
#                end = self.GetInsertionPoint()
#
#                self.GetValue =~ /(\s*[[:graph:]]+\s*)/
#
#                return unless $1
#
#                my start = end - (length $1)
#                self.Remove(start, end)
            pass
        else:
# if (self.GetValue =~ /^con?n?e?c?t? +\w+ +/) {
#     # it's a connection attempt, style the passwd to come out as *****
# }
            evt.Skip()
            return
        self.SetInsertionPointEnd()

class CommandHistory:
    # we keep a list of historical entries, and a 'cursor' so we can
    # keep track of where we are looking in the list.  The last
    # entry in the history gets twiddled as we go.  Once we are done
    # with it and enter it into history, a fresh '' gets appended to
    # the array, on and on, world without end.
    def __init__(self):
        self.history = ['']
        self.current = 0

    # which entry does our 'cursor' point to?
    def current_entry(self, new=''):
        if new != '': self.history[self.current] = new
        return self.history[self.current]

    def prev(self):
        if self.current > 0: self.current -= 1
        return self.current_entry()

    def next(self):
        if self.current < len(self.history)-1: self.current += 1
        return self.current_entry()

    # if we've actually changed anything, take the changed value
    # and use it as the new "current" value, at the end of the array.
    def update(self, string):
        if (self.current_entry() != string):
            self.current = len(self.history)-1
            self.current_entry(string)

    # this is the final state of the thing we input.
    # Make sure it's updated, then push a fresh '' onto the end
    def add(self, string=""):
        if string == "": return # no blank lines pls
        self.history[-1] = string

        self.history.append('')
        self.current = len(self.history)-1
