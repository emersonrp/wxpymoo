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
        self.cmd_history    = CommandHistory(self)
        self.tab_completion = TabCompletion(self)

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

        if k == wx.WXK_UP:
            if self.tab_completion.IsShown():
                self.tab_completion.prev_item()
            else:
                self.SetValue(self.cmd_history.prev())
        elif k == wx.WXK_DOWN:
            if self.tab_completion.IsShown():
                self.tab_completion.next_item()
            else:
                self.SetValue(self.cmd_history.next())
        elif k == wx.WXK_PAGEUP:   self.connection.output_pane.ScrollPages(-1)
        elif k == wx.WXK_PAGEDOWN: self.connection.output_pane.ScrollPages(1)
        elif k == wx.WXK_TAB:      self.fetch_completions()
        elif k == wx.WXK_ESCAPE:   self.tab_completion.Hide()
        elif k == wx.WXK_INSERT:
            if evt.ShiftDown: self.paste_from_selection()

        elif k == wx.WXK_RETURN or k == wx.WXK_NUMPAD_ENTER:
            if self.tab_completion.IsShown():
                self.do_completion(*self.tab_completion.pick_completion())
            else:
                self.send_to_connection(evt)

            # either way:
            self.tab_completion.Hide()

# TODO: this next bit simply doesn't work, but 'home' is not acting right by default
#        elif k == wx.WXK_HOME:
#            print("HOME!")
#            self.SetInsertionPoint(0)

        elif k == 23:  # Ctrl-W
            # TODO - can't test this b/c Ctrl-W is currently auto-bound to Close
            self.change_last_word_to('')
        else:
            self.tab_completion.Hide()
            evt.Skip()
            return
        self.SetInsertionPointEnd()

    def change_last_word_to(self, word):
        new_value = re.sub(self.last_word() + "$", word, self.GetValue());
        self.SetValue(new_value)

    def last_word(self):
        current_value = self.GetValue()
        if not current_value: return
        if current_value.endswith(' '):
            last_word = ''
        else:
            last_word = current_value.split()[-1] # rightmost word/fragment

        return last_word

    def fetch_completions(self):
        self.tab_completion.complete(self.GetValue())

    def do_completion(self, begin_pos, completion):
        if completion:
            self.SetValue(self.GetValue()[:int(begin_pos)] + completion)
            self.SetInsertionPointEnd()

class CommandHistory:
    # we keep a list of historical entries, and a 'cursor' so we can
    # keep track of where we are looking in the list.  The last
    # entry in the history gets twiddled as we go.  Once we are done
    # with it and enter it into history, a fresh '' gets appended to
    # the array, on and on, world without end.
    def __init__(self, parent):
        self.history = ['']
        self.current = 0
        self.parent = parent

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

class TabCompletion(wx.PopupWindow):
    def __init__(self, parent):
        wx.PopupWindow.__init__(self, parent)
        self.verbs = []
        self.names = []
        self.parent = parent
        self.completion_list = None
        self.last_completed = None

    def set_verbs(self, verbs):
        if not verbs: return
        self.verbs = list(set(verbs))
        self.verbs.sort(key = lambda word: word.replace('*', ''))

    def set_names(self, names):
        if not names: return
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

    def pick_completion(self):
        current = self.completion_list.GetFirstSelected()
        return self.begin_pos, self.completion_list.GetItemText(current)

    def next_item(self):
        clist = self.completion_list
        current = clist.GetFirstSelected()
        if current == clist.GetItemCount()-1:
            current = 0
        else:
            current +=1
        clist.Select(current)

    def prev_item(self):
        clist = self.completion_list
        current = clist.GetFirstSelected()
        if current == 0:
            current = clist.GetItemCount()-1
        else:
            current -=1
        clist.Select(current)

    def complete(self, to_complete):
        if not to_complete: return

        # if we've just hit <tab> again without making any changes...
        if to_complete == self.last_completed:
            if not self.IsShown():
                self.Show()
                return
            # ... move the selection 'down' by one...
            self.next_item()

            # ...and do nothing else...
            return

        #... otherwise, carry on
        self.last_completed = to_complete
        # really this is totally.ridiculous.indirection.into.other.modules.innards
        # TODO -- prolly the mcp package should .Initialize and install itself into TabCompletion
        self.parent.connection.mcp.registry.packages['dns-com-vmoo-smartcomplete'].request(self.popup_completions, to_complete)

    def popup_completions(self, begin_pos, completions):
        # do we have one or more completions?
        if completions:

            if len(completions) == 1:
                # we have just the one completion, we should use it
                self.parent.do_completion(begin_pos, completions[0])
            else:
                # there are multiple, clear the listbox, repop it, and show it
                if self.completion_list: self.completion_list.Destroy()

                self.completion_list = CompletionList(self, completions)
                self.begin_pos  = begin_pos

                self.SetSize(self.completion_list.GetSize())

                pos = self.parent.ClientToScreen((5,-5))
                self.Position(pos, (0, self.GetSize()[1]))
                self.Show(True)

        # pressing tab but no completions
        else:
            self.Hide()

class CompletionList(wx.ListCtrl):
    def __init__(self, parent, completions):
        wx.ListCtrl.__init__(self, parent,
            style = wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL
        )

        self.SetTextColour(prefs.get('input_fgcolour'))
        self.SetBackgroundColour(prefs.get('input_bgcolour'))

        font = wx.NullFont
        font.SetNativeFontInfoFromString(prefs.get('input_font'))
        self.SetFont(font)

        self.InsertColumn(0, '')

        for i,c in enumerate(completions):
            self.InsertStringItem(i,c)

        # hoops to jump through to shrink-wrap the list
        height = 0
        for idx in xrange(self.GetItemCount()):
            height += self.GetItemRect(idx).height

        self.SetColumnWidth(0,-1)
        self.SetSize((self.GetColumnWidth(0), height))

        self.Select(0)
