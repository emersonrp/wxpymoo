import wx
import wx.richtext as rtc
import prefs
import re
from utility import platform

class InputPane(rtc.RichTextCtrl):

    def __init__(self, parent, connection):
        rtc.RichTextCtrl.__init__(self, parent,
            style = wx.TE_PROCESS_ENTER | wx.TE_MULTILINE
        )

        self.connection = connection
        self.cmd_history    = CommandHistory()
        self.tab_completion = TabCompletion()

        self.Bind(wx.EVT_TEXT_ENTER, self.send_to_connection )
        self.Bind(wx.EVT_TEXT,       self.update_command_history )
        self.Bind(wx.EVT_KEY_DOWN,   self.check_for_interesting_keystrokes )
##       EVT_CHAR      ( self,     \&debug_key_code )

        if (prefs.get('use_x_copy_paste') == 'True'):
            self.Bind(wx.EVT_MIDDLE_UP                  , self.paste_from_selection )
            self.Bind(rtc.EVT_RICHTEXT_SELECTION_CHANGED, self.copy_from_selection )

        self.Clear()
        self.restyle_thyself()

    def paste_from_selection(self, evt = None):
        uxcp = prefs.get('use_x_copy_paste') == 'True'
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Paste()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)

    def copy_from_selection(self, evt = None):
        uxcp = prefs.get('use_x_copy_paste') == 'True'
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Copy()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)

    def restyle_thyself(self):
        basic_style = rtc.RichTextAttr()
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
            stuff = self.GetValue()
            self.cmd_history.add(stuff)
            self.connection.output(stuff)
            self.Clear()

    def update_command_history(self, evt):
        self.cmd_history.update(self.GetValue())

    def debug_key_code(self, evt):
        k = evt.GetKeyCode()
        # print("EVT_CHAR: " + str(k))

    def check_for_interesting_keystrokes(self, evt):
        k = evt.GetKeyCode()

        if   k == wx.WXK_UP:       self.SetValue(self.cmd_history.prev())
        elif k == wx.WXK_DOWN:     self.SetValue(self.cmd_history.next())
        elif k == wx.WXK_PAGEUP:   self.connection.output_pane.ScrollPages(-1)
        elif k == wx.WXK_PAGEDOWN: self.connection.output_pane.ScrollPages(1)
        elif k == wx.WXK_TAB:      self.offer_completion()
        elif k == wx.WXK_INSERT:
            if evt.ShiftDown: self.paste_from_selection()
        elif k == wx.WXK_RETURN or k == wx.WXK_NUMPAD_ENTER:
            self.send_to_connection(evt)
# TODO: this next bit simply doesn't work, but 'home' is not acting right by default
#        elif k == wx.WXK_HOME:
#            print("HOME!")
#            self.SetInsertionPoint(0)
        elif k == 23:  # Ctrl-W
            # TODO - can't test this b/c Ctrl-W is currently auto-bound to Close
            end = self.GetInsertionPoint()

            m = re.search('(\s*[^\x21-\x7E]+\s*)$', self.GetValue())

            word_to_remove = m.group(1)
            if not word_to_remove: return

            start = end - word_to_remove.len()
            self.Remove(start, end)
        else:
            evt.Skip()
            return
        self.SetInsertionPointEnd()

    def offer_completion(self):
        current_value = self.GetValue()
        if not current_value: return
        if current_value.endswith(' '):
            to_complete = ''
        else:
            to_complete = current_value.split()[-1] # rightmost word/fragment
        completions = self.tab_completion.complete(to_complete)
        if not completions: return
        self.connection.output_pane.display(' '.join(completions))

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
    def current_entry(self):
        return self.history[self.current]

    def set_current(self, string):
        self.history[self.current] = string

    def prev(self):
        if self.current > 0: self.current -= 1
        return self.current_entry()

    def next(self):
        if self.current < len(self.history)-1: self.current += 1
        return self.current_entry()

    # if we've actually changed anything, take the changed value
    # and use it as the new "current" value, at the end of the array.
    def update(self, string):
        string = string.rstrip()
        if (self.current_entry() != string):
            self.current = len(self.history)-1
            self.set_current(string)

    # this is the final state of the thing we input.
    # Make sure it's updated, then push a fresh '' onto the end
    def add(self, string=""):
        string = string.rstrip()

        if string == "": return # no blank lines pls

        # some special cases
        if len(self.history) > 1:
            # if it's a repeat of the very previous one, don't add it
            if string == self.history[-2]:
                self.update('')
                return
        else:
            # no history yet, is it "co username password"?  Don't add it.
            if re.match('^co', string):
                self.update('')
                return

        self.history[-1] = string

        self.current = len(self.history)
        self.history.append('')
        self.update('')

class TabCompletion:
    def __init__(self):
        self.verbs = []
        self.names = []

    def set_verbs(self, verbs):
        self.verbs = list(set(verbs))
        self.verbs.sort(key = lambda word: word.replace('*', ''))

    def set_names(self, names):
        self.names = list(set(names))
        self.names.sort()

    def add_verbs(self, verbs):
        self.set_verbs( self.verbs.append(verbs) )

    def add_names(self, names):
        self.set_names( self.names.append(names) )

    def remove_verbs(self, verbs):
        self.set_verbs( self.verbs.remove(verbs) )

    def remove_names(self, names):
        self.set_names( self.names.remove(names) )

    def complete(self, to_complete):
        print("going to complete " + to_complete)
        completions = []
        for word in self.verbs:
            if word.startswith(to_complete):
                completions.append(word)
        return completions

