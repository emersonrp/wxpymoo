import wx
import wx.richtext as rtc
import prefs
import re
from window.basepane import BasePane
from utility import platform

class InputPane(BasePane):

    def __init__(self, parent, connection):
        BasePane.__init__(self, parent, connection,
            style = wx.TE_PROCESS_ENTER | wx.TE_MULTILINE
        )

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
            if evt.ShiftDown(): self.paste_from_selection()

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

        elif k == ord('W') and evt.CmdDown():  # Ctrl-W
            self.delete_last_word()
        else:
            self.tab_completion.Hide()
            evt.Skip()
            return
        self.SetInsertionPointEnd()

    def delete_last_word(self):
        current_value = self.GetValue()
        if not current_value: return

        new_value = current_value.rsplit(None, 1)[0]

        if new_value == current_value: new_value = ''

        self.SetValue( new_value )

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
            # ...re-show the popup if it's hidden...
            if not self.IsShown():
                self.Show()
                # ...and do nothing else...
                return
            # ...otherwise (wasn't hidden), move the selection 'down' by one...
            self.next_item()

            # ...and do nothing else...
            return

        #... otherwise, carry on
        # TODO -- prolly the mcp package should .Initialize and install itself into TabCompletion
        self.parent.connection.mcp.packages['dns-com-vmoo-smartcomplete'].request(self.popup_completions, to_complete)

    def popup_completions(self, begin_pos, to_complete, completions):

        # do we have one or more new completions for the list?
        if completions:
            self.last_completed = to_complete
            if len(completions) == 1:
                # we have just the one completion, we should use it
                self.parent.do_completion(begin_pos, completions[0])
            else:
                # there are multiple, clear the listbox, repop it, and show it

                if not self.completion_list:
                    self.completion_list = CompletionList(self)

                self.completion_list.fill(completions)
                self.begin_pos = begin_pos

                # TODO - asking about the panel is sorta impolite but sigh wx
                self.SetSize(self.completion_list.panel.GetSize())

                # find the x and y location to pop up the menu
                x_pos, y_pos = self.parent.ClientToScreen((-2,-5))

                # temporarily move the cursor back to begin_pos so we can 
                # find out its relative location.
                self.parent.SetInsertionPoint(long(begin_pos))
                x_pos += self.parent.GetCaret().GetPosition()[0]
                self.parent.SetInsertionPointEnd()

                self.SetPosition((x_pos, y_pos - self.GetSize()[1]))
                self.Show(True)

        # pressing tab but no completions
        else:
            self.last_completed = None
            self.Hide()

class CompletionList(wx.ListCtrl):
    def __init__(self, parent):
        self.panel = wx.Panel(parent)

        wx.ListCtrl.__init__(self, self.panel,
            style = wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL
        )

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self, 1, wx.ALL|wx.EXPAND, 2)
        self.panel.SetSizer(self.sizer)

        self.SetTextColour(prefs.get('fgcolour'))
        self.SetBackgroundColour(prefs.get('bgcolour'))

        font = wx.NullFont
        font.SetNativeFontInfoFromString(prefs.get('font'))
        self.SetFont(font)

    def fill(self, completions):
        self.ClearAll()

        self.InsertColumn(0, '')

        for i,c in enumerate(completions):
            self.InsertStringItem(i,c)

        # hoops to jump through to shrink-wrap the list
        height = 0
        for idx in xrange(self.GetItemCount()):
            height += self.GetItemRect(idx).height

        self.SetColumnWidth(0,-1)

        width = self.GetColumnWidth(0)

        self.panel.SetSize((width + 4, height + 4))
        self.SetSize((width, height))

        self.Select(0)

