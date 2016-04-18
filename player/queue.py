import gi

from gi.repository import Gtk, GObject
from .track import Track
from .util import glob_music
import random


class Queue(GObject.Object):
    __gsignals__ = {
        'update': (GObject.SIGNAL_RUN_FIRST, None, (object, str,)),
        'track': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, app):
        GObject.Object.__init__(self)
        self.app = app

        self.shuffled_list = self.current_list = []
        self.current_track = None
        self.paused = False
        self.disable_change = False
        self.repeat = True
        self.shuffle = False

        app.player.connect("eof", lambda player: self.auto_next())

    def __open_files(self, names, append=False, at=None):
        track_list = [Track(name) for name in names]
        if not append:
            self.shuffled_list = self.current_list = []

        self.__append_tracks(track_list, at)

        if not append:
            if track_list:
                self.current_track = self.shuffled_list[0]
                self.paused = False
                self.app.player.play(self.current_track)
            else:
                self.current_track = None

            self.emit("track", self.current_track)

    def __append_tracks(self, track_list, at=None):
        if not track_list:
            return

        shuffled = track_list
        if self.shuffle:
            shuffled = track_list[:]
            random.shuffle(shuffled)

        if at is not None:
            self.shuffled_list = self.shuffled_list[:at] + shuffled + self.shuffled_list[at:]
            if self.shuffle:
                self.current_list += track_list
            else:
                self.current_list = self.shuffled_list
        else:
            self.shuffled_list += shuffled

        self.app.discoverer.add(track_list)
        self.emit("update", self.shuffled_list, "append")

    def open_files(self, files):
        self.__open_files(glob_music(files))

    def append_files(self, files, at=None):
        self.__open_files(glob_music(files), append=True, at=at)

    def reoder(self, from_indices, to_pos):
        tracks = []
        for index in from_indices:
            tracks.append(self.shuffled_list[index])
            if index < to_pos:
                to_pos -= 1

        from_indices.sort()
        from_indices.reverse()
        for index in from_indices:
            del self.shuffled_list[index]

        self.shuffled_list = self.shuffled_list[:to_pos] + tracks + self.shuffled_list[to_pos:]
        if not self.shuffle:
            self.current_list = self.shuffled_list
        self.emit("update", self.shuffled_list, "reorder")

        return to_pos

    def remove(self, indices):
        new_list = []
        removed = set()
        current_track_attempt = self.current_track

        for index in indices:
            removed.add(index)

        if self.shuffle:
            tracks = [self.shuffled_list[index] for index in indices]
            for track in tracks:
                self.current_list.remove(track)

        for index, track in enumerate(self.shuffled_list):
            if index in removed:
                if track is current_track_attempt:
                    if len(self.shuffled_list) > index + 1:
                        current_track_attempt = self.shuffled_list[index + 1]
                    else:
                        current_track_attempt = None
            else:
                new_list.append(track)

        self.shuffled_list = new_list

        if current_track_attempt is None and len(self.shuffled_list) > 0:
            current_track_attempt = self.shuffled_list[0]

        self.emit("update", self.shuffled_list, "remove")

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
        cur = self.shuffled_list.index(self.current_track)
        cur += 1
        if cur >= len(self.shuffled_list):
            if not allow_at_end:
                return
            cur = 0
        self.set_current(self.shuffled_list[cur])

    def previous(self):
        if self.disable_change:
            return
        cur = self.shuffled_list.index(self.current_track)
        cur -= 1
        if cur < 0:
            cur = len(self.shuffled_list) - 1
        self.set_current(self.shuffled_list[cur])

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

    def toggle_shuffle(self, shuffle):
        self.shuffle = shuffle

        if shuffle:
            self.shuffled_list = self.current_list[:]
            random.shuffle(self.shuffled_list)
        else:
            self.shuffled_list = self.current_list

        self.emit("update", self.shuffled_list, "shuffle")
