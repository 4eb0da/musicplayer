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
        self.paused = False
        self.disable_change = False

        app.player.connect("eof", lambda player: self.next())

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
            self.paused = False

            self.app.player.play(self.current_track)
        else:
            self.current_track = None

        self.emit('track', self.current_track)

        self.app.discoverer.add(track_list)

    def set_current(self, track):
        if self.disable_change:
            return
        for tr in self.current_list:
            if tr == track:
                self.paused = False
                self.current_track = track
                self.emit('track', self.current_track)
                self.app.player.play(self.current_track)
                return

    def next(self):
        if self.disable_change:
            return
        cur = self.current_list.index(self.current_track)
        cur += 1
        if cur >= len(self.current_list):
            cur = 0
        self.set_current(self.current_list[cur])

    def previous(self):
        if self.disable_change:
            return
        cur = self.current_list.index(self.current_track)
        cur -= 1
        if cur < 0:
            cur = len(self.current_list) - 1
        self.set_current(self.current_list[cur])

    def play_pause(self):
        if self.paused:
            self.paused = False
            self.app.player.resume()
        else:
            self.paused = True
            self.app.player.pause()

    def is_paused(self):
        return self.paused

    def toggle_change(self, toggle):
        self.disable_change = not toggle
