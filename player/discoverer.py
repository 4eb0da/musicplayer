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

    PACK_LIMIT = 35

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

                self.wait_idle()
                items = [track for track in self.queue if not track.info and not track.incorrect_info]
                self.queue = []

            pack = []
            for track in items:
                tags = taglib.File(track.fullpath).tags
                track.info = TrackInfo(track.fullpath, tags)
                pack.append(track)
                if len(pack) == self.PACK_LIMIT:
                    GObject.idle_add(self.emit, "info", pack)
                    pack = []
                GObject.idle_add(self.emit, "info", pack)
                self.wait_idle()
            if len(pack):
                GObject.idle_add(self.emit, "info", pack)

    def wait_idle(self):
        with self.condition:
            def notify():
                with self.condition:
                    self.condition.notify()
            GObject.idle_add(notify)
            self.condition.wait()

    def add(self, tracks):
        with self.condition:
            self.queue += tracks
            self.condition.notify()
