import gi

from gi.repository import Gtk, GObject
from .track import Track
from .util import glob_music
from .dirreader.dirreader import DirReader
import random


class Queue(GObject.Object):
    __gsignals__ = {
        'start': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'stop': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'insert': (GObject.SIGNAL_RUN_FIRST, None, (object, int,)),
        'delete': (GObject.SIGNAL_RUN_FIRST, None, (int, int,)),
        'track': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'play_pause': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'shuffle': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'repeat': (GObject.SIGNAL_RUN_FIRST, None, (bool,))
    }

    def __init__(self, app):
        GObject.Object.__init__(self)
        self.app = app

        self.shuffled_list = self.current_list = []
        self.current_track = None
        self.paused = False
        self.disable_change = False
        self.repeat = app.settings.getboolean("queue", "repeat", True)
        self.shuffle = app.settings.getboolean("queue", "shuffle", False)
        self.read_id = 0
        self.flush_read_id = 0
        self.reader = DirReader()

        if self.shuffle:
            self.shuffled_list = []

        app.player.connect("eof", lambda player: self.auto_next())
        app.player.connect("error", self.on_error)
        self.reader.connect("files", self.on_files_found)

    def __open_files(self, names, append=False, at=None):
        track_list = [Track(name) for name in names]
        if not append:
            length = len(self.current_list)
            self.shuffled_list = self.current_list = []
            self.emit("delete", length, 0)

        self.__append_tracks(track_list, at)

        if not append or not self.current_track:
            if track_list:
                self.current_track = self.shuffled_list[0]
                self.paused = False
                self.app.player.play(self.current_track)
            else:
                self.current_track = None

            self.emit("track", self.current_track)
            self.emit("play_pause", True)
            self.emit("start")

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
            at = len(self.shuffled_list)
            self.shuffled_list += shuffled
            if self.shuffle:
                self.current_list += track_list

        self.app.discoverer.add(track_list)
        self.emit("insert", shuffled, at)

    def open_files(self, files):
        if len(self.current_list):
            self.remove(range(0, len(self.current_list)))

        self.read_id += 1
        self.flush_read_id = self.read_id
        self.reader.open(files, self.read_id, True, -1)

    def append_files(self, files, at=None):
        # todo make "at" async
        if at is not None:
            self.__open_files(glob_music(files), append=True, at=at)
            return

        self.read_id += 1
        # self.flush_read_id = self.read_id
        self.reader.open(files, self.read_id, False, at=-1 if not at else at)

    def on_error(self, player):
        if self.current_track:
            self.current_track.has_error = True
        self.auto_next()

    def on_files_found(self, reader, files, job_id, at):
        if job_id < self.flush_read_id:
            return

        self.__open_files(files, append=True, at=None if at == -1 else at)

    def get_tracks(self):
        return self.shuffled_list

    def reorder(self, from_indices, to_pos):
        if to_pos is None:
            to_pos = len(self.shuffled_list)

        tracks = []
        for index in from_indices:
            tracks.append(self.shuffled_list[index])
            if index < to_pos:
                to_pos -= 1

        for index in reversed(from_indices):
            self.emit("delete", 1, index)

        from_indices.sort()
        from_indices.reverse()
        for index in from_indices:
            del self.shuffled_list[index]

        self.shuffled_list = self.shuffled_list[:to_pos] + tracks + self.shuffled_list[to_pos:]
        if not self.shuffle:
            self.current_list = self.shuffled_list
        self.emit("insert", tracks, to_pos)

        return to_pos

    def remove(self, indices):
        new_list = []
        removed = set()
        current_track_attempt = self.current_track

        for index in indices:
            removed.add(index)

        for index in reversed(indices):
            self.emit("delete", 1, index)

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
        if not self.shuffle:
            self.current_list = self.shuffled_list

        if current_track_attempt is None and len(self.shuffled_list) > 0:
            current_track_attempt = self.shuffled_list[0]

        if current_track_attempt is not self.current_track:
            if current_track_attempt is not None and current_track_attempt.has_error:
                self.current_track = current_track_attempt
                self.next()
            else:
                self.set_current(current_track_attempt)

    def set_current(self, track):
        if self.disable_change:
            return

        self.paused = not track
        self.current_track = track
        self.emit("track", self.current_track)
        self.emit("play_pause", bool(track))
        self.app.player.play(self.current_track)

    def auto_next(self):
        self.next(allow_at_end=self.repeat)

    def next(self, allow_at_end=True):
        self.__find_next_track(1, allow_at_end=allow_at_end)

    def previous(self):
        self.__find_next_track(-1)

    def __find_next_track(self, direction, allow_at_end=True):
        length = len(self.shuffled_list)
        if self.disable_change or length == 1:
            return

        if len(self.shuffled_list) == 0:
            return

        if not self.current_track:
            self.set_current(self.shuffled_list[0])

        start = cur = self.shuffled_list.index(self.current_track)
        cur = (cur + direction) % length
        while self.shuffled_list[cur].has_error:
            cur = (cur + direction) % length
            if cur == start or not allow_at_end and cur + 1 == length:
                if self.current_track.has_error or cur != start:
                    self.set_current(None)
                else:
                    self.set_current(self.current_track)
                return

        self.set_current(self.shuffled_list[cur])

    def play_pause(self, play=None):
        if play is None:
            play = self.paused

        if play:
            if self.current_track:
                self.paused = False
                self.app.player.resume()
                self.emit("play_pause", True)
        else:
            self.paused = True
            self.app.player.pause()
            self.emit("play_pause", False)

    def is_paused(self):
        return self.paused

    def toggle_change(self, toggle):
        self.disable_change = not toggle

    def toggle_repeat(self, repeat):
        self.repeat = repeat
        self.app.settings.setboolean("queue", "repeat", repeat)
        self.emit("repeat", repeat)

    def toggle_shuffle(self, shuffle):
        self.shuffle = shuffle

        if shuffle:
            self.shuffled_list = self.current_list[:]
            random.shuffle(self.shuffled_list)
        else:
            self.shuffled_list = self.current_list

        self.emit("delete", len(self.shuffled_list), 0)
        self.emit("insert", self.shuffled_list, 0)

        self.app.settings.setboolean("queue", "shuffle", shuffle)
        self.emit("shuffle", shuffle)
