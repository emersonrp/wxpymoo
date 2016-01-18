import wx
import wx.html

import prefs
from worlds import worlds

class WorldsList(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, name = 'Worlds List', style = wx.RESIZE_BORDER)

        self.connection = parent.connection

        world_details_staticbox = wx.StaticBox(self)
        world_details_box       = wx.StaticBoxSizer(world_details_staticbox, wx.HORIZONTAL)

        world_label  = wx.StaticText(self, label = "World")
        self.world_picker = wx.Choice(self, style = wx.CB_SORT )

        for world in worlds: self.world_picker.Append(world)

        world_picker_sizer = wx.BoxSizer(wx.HORIZONTAL)
        world_picker_sizer.Add(world_label,  0,         wx.ALIGN_CENTER_VERTICAL, 0)
        world_picker_sizer.Add(self.world_picker, 1, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)

        self.world_details_panel = WorldPanel(self)
        world_details_box.Add(self.world_details_panel, 1, wx.EXPAND, 0)

        button_sizer = self.CreateButtonSizer( wx.OK | wx.CANCEL )

        # Hax: change the "OK" button to "Connect"
        # This is a hoop-jumping exercise to use the platform-specific locations
        # of "OK" and "Cancel" instead of the hoop-jumping exercise of making my
        # own buttons.  There's almost certainly a better way to do this.
        for b in button_sizer.GetChildren():
            bwin = b.GetWindow()
            if (not bwin) or (bwin.GetLabel() != '&OK'): continue
            bwin.SetLabel('&Connect')
            break

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(world_picker_sizer, 0, wx.EXPAND | wx.ALL,            10)
        main_sizer.Add(world_details_box,  1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        main_sizer.Add(button_sizer,       0, wx.EXPAND | wx.ALL,            10)

        last_world_name = prefs.get('last_world')
        last_world = self.world_picker.FindString(last_world_name)
        # if we no longer have that world, go back to the top of the list
        if last_world < 0:
            last_world_name = self.world_picker.GetString(0)
            last_world = self.world_picker.FindString(last_world_name)

        self.world_picker.SetSelection(last_world)
        self.world_details_panel.fill_thyself(worlds[last_world_name])

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CHOICE, self.select_world, self.world_picker)
        self.Bind(wx.EVT_BUTTON, self.on_connect, id = wx.ID_OK)


    def select_world(self, evt):
        world = worlds[self.world_picker.GetStringSelection()]
        self.world_details_panel.fill_thyself(world)

    # TODO - make WxMOO.World have a notion of "connect to yourself"
    # Also therefore merge WxMOO.World and WxMOO.Window.WorldPanel
    def on_connect(self, evt):
        self.connection.connect(self.world_details_panel.world)
        self.Hide()


class WorldPanel(wx.Panel):

    import prefs

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        name_label = wx.StaticText(self, label = "Name:")
        host_label = wx.StaticText(self, label = "Host:")
        port_label = wx.StaticText(self, label = "Port:")
        self.name = wx.TextCtrl(self)
        self.host = wx.TextCtrl(self)
        self.port = wx.SpinCtrl(self)
        self.port.SetRange(0, 65535)
        self.port.SetValue(7777)

        username_label = wx.StaticText(self, label = "Username:")
        password_label = wx.StaticText(self, label = "Password:")
        type_label = wx.StaticText(self, label = "Type:")
        self.username = wx.TextCtrl(self)
        self.password = wx.TextCtrl(self, style = wx.TE_PASSWORD)
        self.conntype = wx.Choice  (self, choices = ['Socket','SSL','SSH Forwarding'] )
        self.conntype.SetSelection(0)

        self.ssh_username_label = wx.StaticText(self, label = "SSH Username:")
        self.ssh_loc_host_label = wx.StaticText(self, label = "SSH Host:")
        self.ssh_username       = wx.TextCtrl(self)
        self.ssh_loc_host       = wx.TextCtrl(self)

        field_sizer = wx.FlexGridSizer(cols = 2, hgap = 5, vgap = 10)
        field_sizer.Add(name_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.name, 0, wx.EXPAND, 0)
        field_sizer.Add(host_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.host, 0, wx.EXPAND, 0)
        field_sizer.Add(port_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.port, 0, wx.EXPAND, 0)
        field_sizer.Add(username_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.username, 0, wx.EXPAND, 0)
        field_sizer.Add(password_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.password, 0, wx.EXPAND, 0)
        field_sizer.Add(type_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.conntype, 0, wx.EXPAND, 0)
        field_sizer.Add(self.ssh_username_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.ssh_username, 0, wx.EXPAND, 0)
        field_sizer.Add(self.ssh_loc_host_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        field_sizer.Add(self.ssh_loc_host, 0, wx.EXPAND, 0)
        field_sizer.AddGrowableCol(1)

        self.desc = wx.html.HtmlWindow(self)
        self.desc.SetBorders(0)
        desc_box = wx.StaticBoxSizer(wx.StaticBox(self, label = "description"), wx.HORIZONTAL)
        desc_box.Add(self.desc, 1, wx.EXPAND, 0)

        self.note = wx.TextCtrl(self, style = wx.TE_MULTILINE)
        note_box = wx.StaticBoxSizer(wx.StaticBox(self, label = "notes"), wx.HORIZONTAL)
        note_box.Add(self.note, 1, wx.EXPAND, 0)

        mcp_check          = wx.CheckBox(self, label = "MCP 2.1")
        login_dialog_check = wx.CheckBox(self, label = "Use Login Dialog")
        shortlist_check    = wx.CheckBox(self, label = "On Short List")
        checkbox_sizer = wx.GridSizer(3, 2, 0, 0)
        checkbox_sizer.Add(mcp_check, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        checkbox_sizer.Add(login_dialog_check, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        checkbox_sizer.Add(shortlist_check, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)

        new_button   = wx.Button(self, label = "New")
        reset_button = wx.Button(self, label = "Reset")
        save_button  = wx.Button(self, label = "Save")
        button_sizer = wx.FlexGridSizer(cols = 3, rows = 1, hgap = 0, vgap = 0)
        button_sizer.Add(new_button, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        button_sizer.Add(reset_button, 0, wx.ALL, 5)
        button_sizer.Add(save_button, 0, wx.ALL, 5)
        button_sizer.AddGrowableCol(0)

        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel_sizer.Add(field_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.panel_sizer.Add(desc_box, 1, wx.EXPAND, 0)
        self.panel_sizer.Add(note_box, 1, wx.EXPAND, 0)
        self.panel_sizer.Add(checkbox_sizer, 0, wx.EXPAND, 0)
        self.panel_sizer.Add(button_sizer, 0, wx.EXPAND, 0)

        self.SetSizerAndFit(self.panel_sizer)

        self.Bind(wx.EVT_CHOICE, self.show_ssh_fields_if_appropriate)

        self.show_ssh_fields_if_appropriate()

    def on_save(self, evt): pass

    def on_reset(self, evt): pass

    def on_new(self, evt): pass

    def fill_thyself(self, world):
        self.world = world

        self.name.SetValue(unicode(world.get("name")))
        if world.get('host')        : self.host.SetValue(unicode(world.get("host")))
        if world.get('port')        : self.port.SetValue(int(world.get("port")))
        if world.get('username')    : self.username.SetValue(world.get("username"))
        if world.get('password')    : self.password.SetValue(world.get("password"))
        if world.get('description') : self.desc.SetPage(world.get('description'))
        if world.get('note')        : self.note.SetValue(unicode(world.get("note")))
        self.conntype.SetSelection(world.get("conntype") or 0)

        if world.get('ssh_username'): self.ssh_username.SetValue(world.get("ssh_username"))
        if world.get('ssh_loc_host'): self.ssh_loc_host.SetValue(world.get("ssh_loc_host"))

        self.show_ssh_fields_if_appropriate()

    def show_ssh_fields_if_appropriate(self, evt = None):
        to_show = self.conntype.GetSelection() == 2
        self.ssh_username_label.Show(to_show)
        self.ssh_loc_host_label.Show(to_show)
        self.ssh_username.Show(to_show)
        self.ssh_loc_host.Show(to_show)

        self.panel_sizer.Layout()
