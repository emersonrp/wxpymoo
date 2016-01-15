import wx
import re

class World(dict):
    _fields = '''
        name host port user pass note type
        ssh_server ssh_user ssh_loc_host ssh_loc_port
        ssh_rem_host ssh_rem_port
    '''.split()

    _defaults = {
        'port' : 7777,
        'type' : 0,   # Socket
    }

    def __init__(self, data):
        data = data or World._defaults
        for f in World._fields:
            if data.get(f) is not None: self[f] = data.get(f)

    def save(self):
        global _config
        worldname = re.sub(r'\W', '_', self.get('name'))

        _config.SetPath(worldname)

        for f in World._fields:
            if self.get(f) is not None: _config.Write(f, unicode(self.get(f)))

        _config.SetPath('/')

worlds    = {}
_defaults = { }
_config = wx.FileConfig(localFilename = '.wxpymoo_worlds')

g_more, worldname, g_index = _config.GetFirstGroup()
while g_more:
    _config.SetPath(worldname)

    worlddata = {}

    e_more, dataname, e_index = _config.GetFirstEntry()
    while e_more:
        worlddata[dataname] = _config.Read(dataname)
        e_more, dataname, e_index = _config.GetNextEntry(e_index)

    worlds[worldname] = World(worlddata)
    g_more, worldname, g_index = _config.GetNextGroup(g_index)
    _config.SetPath('/')

else:
    import json
    init_worlds = json.load(open('moolist.json','r'))

    for world_data in init_worlds:
        world = World(world_data)
        world.save()
        worlds[world.get('name')] = world

