import wx
import wx.richtext as rtc
import prefs
import re
from window.basepane import BasePane
from utility import platform
from theme import Theme

class InputPane(BasePane):

    def __init__(self, parent, connection):
        BasePane.__init__(self, parent, connection,
            style = wx.TE_PROCESS_ENTER | wx.TE_MULTILINE
        )

        self.cmd_history    = CommandHistory(self)
        self.tab_completion = TabCompletion(self, connection)

        self.tabs = wx.GetApp().GetTopWindow().tabs

        self.Bind(wx.EVT_TEXT_ENTER, self.send_to_connection )
        self.Bind(wx.EVT_TEXT,       self.onTextChange )
        self.Bind(wx.EVT_KEY_DOWN,   self.check_for_interesting_keystrokes )
        self.Bind(wx.EVT_CHAR_HOOK,  self.do_keyboard_copy )

        self.AddClearAllToMenu()

        self.Clear()
        self.restyle_thyself()

    def do_keyboard_copy(self, evt):
        if evt.CmdDown():
            k = evt.GetKeyCode()
            if k == 67:
                self.GetTopLevelParent().handleCopy(evt)
                return
            #if k == 86: print("That was a Cmd-V")
            #if k == 88: print("That was a Cmd-X")
        evt.Skip()

    def doClear(self, evt): self.Clear()
    def AddClearAllToMenu(self):
        menu = self.GetContextMenu()
        selectall, selectall_pos = menu.FindChildItem(menu.FindItem("Select All"))
        clear_input = menu.Insert(selectall_pos, -1, "Clear Input", "Clears all text from the input")
        self.Bind(wx.EVT_MENU, self.doClear, clear_input)
        self.SetContextMenu(menu)

    def paste_from_selection(self, evt = None):
        uxcp = prefs.get('use_x_copy_paste')
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Paste()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)

    def copy_from_selection(self, evt = None):
        uxcp = prefs.get('use_x_copy_paste')
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Copy()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)

    ### HANDLERS
    def send_to_connection(self, evt):
        if self.connection:
            stuff = self.GetValue()
            self.cmd_history.add(stuff)
            self.connection.output(stuff + "\n")
            self.Clear()
            if prefs.get('local_echo') and (not 'ECHO' in self.connection.iac or self.connection.iac['ECHO'] == True):
                self.connection.output_pane.display(">" + stuff + "\n")

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
        elif k == wx.WXK_ESCAPE:   self.tab_completion.CloseAndClear()
        elif k == wx.WXK_INSERT:
            if evt.ShiftDown(): self.paste_from_selection()

        elif k == wx.WXK_RETURN or k == wx.WXK_NUMPAD_ENTER:
            if self.tab_completion.IsShown():
                self.do_completion(*self.tab_completion.pick_completion())
            else:
                self.send_to_connection(evt)

            # either way:
            self.tab_completion.CloseAndClear()

        # TODO: this next bit simply doesn't work, but 'home' is not acting right by default
#        elif k == wx.WXK_HOME:
#            print("HOME!")
#            self.SetInsertionPoint(0)

        # Cmd-[#] to switch directly to a tab -- includes 1234567890-= keys
        # this is a little confusing because the tab indices are zero-based, so 
        # we want key [1] to turn into a 0.
        elif evt.CmdDown() and (k in (49,50,51,52,53,54,55,56,57,48,45,61)):

            # for [1]-[9], we want indices 0-8, so subtract 49 from k to get that
            page_index = k - 49
            if (k == 48): page_index = 9  # [0]
            if (k == 45): page_index = 10 # [-]
            if (k == 61): page_index = 11 # [=]
            if (page_index > self.tabs.GetPageCount()): return

            # if we're re-selecting the current one, pop back to the last one
            # this behavior copped from weechat
            if (page_index == self.tabs.GetSelection()):
                page_index = self.tabs.last_selection

            self.tabs.last_selection = self.tabs.SetSelection(page_index)

        # Cmd-Left / Cmd-Right to switch tabs
        elif (evt.CmdDown() and (k == wx.WXK_LEFT or k == wx.WXK_RIGHT)):
            self.tabs.AdvanceSelection(k == wx.WXK_RIGHT)

        elif k == ord('W') and evt.CmdDown():  # Ctrl-W
            self.delete_last_word()
        else:
        #    self.tab_completion.CloseAndClear()
            evt.Skip()
            return
        self.SetInsertionPointEnd()

    def onTextChange(self, evt):
        self.cmd_history.update(self.GetValue())
        if self.GetValue() == '':
            self.tab_completion.CloseAndClear()
        if self.tab_completion.IsShown():
            evt.Skip()
            self.fetch_completions()

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
            self.tab_completion.CloseAndClear()
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
    def __init__(self, parent, connection):
        wx.PopupWindow.__init__(self, parent,
            flags = wx.BORDER_SIMPLE
        )
        self.verbs = []
        self.names = []
        self.parent = parent
        self.completers = None
        self.completion_list = CompletionList(self)
        self.last_completed = None
        self.connection = connection
        self.SetBackgroundColour(Theme.fetch().get('foreground'))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.completion_list, 1, wx.ALL|wx.EXPAND, 2)
        self.SetSizer(sizer)

    def pick_completion(self):
        current = self.completion_list.GetFirstSelected()
        return self.begin_pos, self.completion_list.GetItemText(current)

    def CloseAndClear(self):
        self.Hide()
        if self.completion_list:
            self.completion_list.ClearAll()

    def next_item(self):
        clist = self.completion_list
        current = clist.GetFirstSelected()
        if current == clist.GetItemCount()-1:
            current = 0
        else:
            current +=1
        clist.Select(current)
        clist.EnsureVisible(current)

    def prev_item(self):
        clist = self.completion_list
        current = clist.GetFirstSelected()
        if current == 0:
            current = clist.GetItemCount()-1
        else:
            current -=1
        clist.Select(current)
        clist.EnsureVisible(current)

    def complete(self, to_complete):
        if not to_complete: return

        # if we've just hit <tab> again without making any changes...
        if self.last_completed and (to_complete == self.last_completed):
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
        # TODO - so far we only have the one possible completer but maybe later we'll select from options
        if self.completers:
            self.completers.request(self.popup_completions, to_complete)

    def popup_completions(self, begin_pos, to_complete, completions):

        # do we have one or more new completions for the list?
        if completions:
            # populate the list in every case
            self.completion_list.fill(completions)
            self.begin_pos = begin_pos
            self.last_completed = to_complete

            if len(completions) == 1:
                # we have just the one completion, we should use it
                self.parent.do_completion(begin_pos, completions[0])
                self.last_completed = None
            else:
                # there are multiple, format and show the list
                w, h = self.completion_list.GetSize()
                avail_height = min( h, self.connection.output_pane.GetSize()[1])

                # if we're gonna have a vertical scrollbar, make room
                if h > avail_height:
                    w = w + 15

                adj = 1
                if platform == "windows": adj = 10
                self.SetSize((w + adj, avail_height))
                self.Layout()

                # find the x and y location to pop up the menu
                x_pos, y_pos = self.parent.ClientToScreen((-2,-5))

                # temporarily move the cursor back to begin_pos so we can 
                # find out where, along the 'x' axis, the text being completed
                # actually begins
                self.parent.SetInsertionPoint(int(begin_pos))
                x_pos += self.parent.GetCaret().GetPosition()[0]
                self.parent.SetInsertionPointEnd()

                self.SetPosition((x_pos, y_pos - avail_height))
                self.Show(True)

        # pressing tab but no completions
        else:
            self.last_completed = None
            self.CloseAndClear()

class CompletionList(wx.ListCtrl):
    def __init__(self, parent):

        wx.ListCtrl.__init__(self, parent,
            style = wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL
        )

        self.parent = parent

        self.SetTextColour(Theme.fetch().get('foreground'))
        self.SetBackgroundColour(Theme.fetch().get('background'))

        font = wx.Font(prefs.get('font'))
        self.SetFont(font)

        self.Bind(wx.EVT_KEY_DOWN,   self.parent.parent.check_for_interesting_keystrokes )

    def fill(self, completions):
        self.ClearAll()

        self.InsertColumn(0, '')

        for i,c in enumerate(completions):
            self.InsertItem(i,c)

        # hoops to jump through to shrink-wrap the list
        height = 10
        for idx in range(self.GetItemCount()):
            height += self.GetItemRect(idx).height

        self.SetColumnWidth(0,-1)
        self.SetSize((self.GetColumnWidth(0) + 5, height))

        self.Select(0)

