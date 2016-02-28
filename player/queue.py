import gi

from gi.repository import Gtk, GObject
from .track import Track
from .util import glob_music

class Queue(GObject.Object):
    __gsignals__ = {
        'update': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'track': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, app):
        GObject.Object.__init__(self)
        self.app = app

        self.current_list = []
        self.current_track = None

    def open_files(self, names):
        track_list = [Track(name) for name in names]
        self.set_list(track_list)

    def open_dir(self, dir):
        self.open_files(glob_music(dir))

    def set_list(self, track_list):
        self.current_list = track_list
        self.emit('update', track_list)

        if track_list:
            self.current_track = track_list[0]

            self.app.player.play(self.current_track)
        else:
            self.current_track = None

        self.emit('track', self.current_track)

        self.app.discoverer.add(track_list)

    def set_current(self, track):
        for tr in self.current_list:
            if tr == track:
                self.current_track = track
                self.app.player.play(self.current_track)
                return
