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
        self.repeat = True

        app.player.connect("eof", lambda player: self.auto_next())

    def __open_files(self, names, append=False):
        track_list = [Track(name) for name in names]
        if append:
            self.current_list += track_list
            self.emit("update", self.current_list)
            self.app.discoverer.add(track_list)
        else:
            self.set_list(track_list)

    def open_files(self, files):
        self.__open_files(glob_music(files))

    def append_files(self, files):
        self.__open_files(glob_music(files), True)

    def set_list(self, track_list):
        self.current_list = track_list
        self.emit("update", track_list)

        if track_list:
            self.current_track = track_list[0]
            self.paused = False

            self.app.player.play(self.current_track)
        else:
            self.current_track = None

        self.emit("track", self.current_track)

        self.app.discoverer.add(track_list)

    def reoder(self, from_indices, to_pos):
        tracks = []
        for index in from_indices:
            tracks.append(self.current_list[index])
            if index < to_pos:
                to_pos -= 1

        from_indices.sort()
        from_indices.reverse()
        for index in from_indices:
            del self.current_list[index]

        self.current_list = self.current_list[:to_pos] + tracks + self.current_list[to_pos:]
        self.emit("update", self.current_list)

        return to_pos

    def remove(self, indices):
        new_list = []
        removed_dict = {}
        current_track_attempt = self.current_track

        for index in indices:
            removed_dict[index] = True

        for index, track in enumerate(self.current_list):
            if index in removed_dict:
                if track is current_track_attempt:
                    if len(self.current_list) > index + 1:
                        current_track_attempt = self.current_list[index + 1]
                    else:
                        current_track_attempt = None
            else:
                new_list.append(track)

        self.current_list = new_list

        if current_track_attempt is None and len(self.current_list) > 0:
            current_track_attempt = self.current_list[0]

        self.emit("update", self.current_list)

        if current_track_attempt is not self.current_track and current_track_attempt is not None:
            self.set_current(current_track_attempt)

    def set_current(self, track):
        if self.disable_change:
            return

        self.paused = False
        self.current_track = track
        self.emit("track", self.current_track)
        self.app.player.play(self.current_track)

    def auto_next(self):
        self.next(allow_at_end=self.repeat)

    def next(self, allow_at_end=True):
        if self.disable_change:
            return
        cur = self.current_list.index(self.current_track)
        cur += 1
        if cur >= len(self.current_list):
            if not allow_at_end:
                return
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

    def toggle_repeat(self, repeat):
        self.repeat = repeat
