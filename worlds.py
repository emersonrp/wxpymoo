import wx
import re
import os

class World(dict):

    _defaults = {
        'port'     : '7777',
    }

    def __init__(self, data):
        data = data or World._defaults
        for f in data:
            if data.get(f) is not None: self[f] = data.get(f)

    def save(self):
        global _config
        worldname = re.sub(r'\W', '_', self.get('name'))

        _config.DeleteGroup(worldname)
        _config.SetPath(worldname)

        for f in self:
            if self.get(f): _config.Write(f, unicode(self.get(f)))

        _config.SetPath('/')
        _config.Flush()

worlds    = {}
_defaults = { }
_config = wx.FileConfig(localFilename = '.wxpymoo_worlds')

# loop worlds...
g_more, worldname, g_index = _config.GetFirstGroup()
while g_more:
    _config.SetPath(worldname)

    worlddata = {}

    # loop data lines inside each world....
    e_more, dataname, e_index = _config.GetFirstEntry()
    while e_more:
        worlddata[dataname] = _config.Read(dataname)
        e_more, dataname, e_index = _config.GetNextEntry(e_index)

    # build the World object
    worlds[worlddata['name']] = World(worlddata)

    # carry on, back to the top for the next world
    _config.SetPath('/')
    g_more, worldname, g_index = _config.GetNextGroup(g_index)

else:
    import json
    path = wx.GetApp().path
    initial_worlds = json.load(open(os.path.join(path, 'initial_worlds.json'),'r'))

    for world_data in initial_worlds:
        world = World(world_data)
        world.save()
        worlds[world.get('name')] = world

