import taglib
import gi

gi.require_version("Gtk", "3.0")

from threading import Thread, Condition
from gi.repository import Gtk, GObject
from .trackinfo import TrackInfo


class Discoverer(GObject.Object):
    __gsignals__ = {
        'info': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self):
        GObject.Object.__init__(self)

        self.queue = []
        self.condition = Condition()
        self.thread = Thread(target=self.discover, args=())
        self.thread.daemon = True
        self.thread.start()

    def discover(self):
        while True:
            with self.condition:
                if not(len(self.queue)):
                    self.condition.wait()
                items = [track for track in self.queue if not track.info and not track.incorrect_info]
                self.queue = []
            for track in items:
                tags = taglib.File(track.fullpath).tags
                if TrackInfo.check_tags(tags):
                    track.info = TrackInfo(tags)
                    GObject.idle_add(self.emit, "info", track)
                else:
                    track.incorrect_info = True

    def add(self, tracks):
        with self.condition:
            self.queue += tracks
            self.condition.notify()
