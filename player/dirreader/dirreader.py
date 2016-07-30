import gi

gi.require_version("Gtk", "3.0")

from threading import Thread, Condition
from gi.repository import Gtk, GObject
from ..util import filter_music
import os

class DirReader(GObject.Object):
    __gsignals__ = {
        'files': (GObject.SIGNAL_RUN_FIRST, None, (object,int,int,))
    }

    PACK_LIMIT = 50

    def __init__(self):
        GObject.Object.__init__(self)

        self.queue = []
        self.flush_queue = None
        self.condition = Condition()
        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def open(self, dirs, job_id, empty, at):
        with self.condition:
            if empty:
                self.queue = []
                self.flush_queue = job_id

            self.queue += [{
                               "directory": directory,
                               "job_id": job_id,
                               "at": at
                           } for directory in dirs]
            self.condition.notify()

    def run(self):
        while True:
            self.process()

    def process(self):
        path = None
        job_id = None
        at = None

        with self.condition:
            if not (len(self.queue)):
                self.condition.wait()

            self.wait_idle()

            if len(self.queue):
                path = self.queue[0]["directory"]
                job_id = self.queue[0]["job_id"]
                at = self.queue[0]["at"]
                self.queue = self.queue[1:]
                if self.flush_queue is not None and job_id < self.flush_queue:
                    return

        pack = []

        if os.path.isdir(path):
            for root, dirnames, filenames in os.walk(path):
                filenames.sort()
                for file in filenames:
                    if not filter_music(file):
                        continue
                    pack.append(os.path.join(os.getcwd(), root, file))

                    if len(pack) >= self.PACK_LIMIT:
                        GObject.idle_add(self.emit, "files", pack, job_id, at)
                        pack = []
                        with self.condition:
                            if self.flush_queue is not None and job_id < self.flush_queue:
                                return
                        self.wait_idle()
        elif filter_music(path):
            pack.append(path)

        if len(pack):
            GObject.idle_add(self.emit, "files", pack, job_id, at)

    def wait_idle(self):
        with self.condition:
            def notify():
                with self.condition:
                    self.condition.notify()
            GObject.idle_add(notify)
            self.condition.wait()
