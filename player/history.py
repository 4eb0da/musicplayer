from gi.repository import GObject


class History(GObject.Object):
    __gsignals__ = {
        'append': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'clear': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'change_current': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
    }

    def __init__(self, app):
        GObject.Object.__init__(self)

        self.__app = app
        self.__history = []
        self.__current_id = -1
        # todo remake it
        self.__changing_track_list = False

        app.queue.connect("update", self.__on_update)
        app.discoverer.connect("end", self.__on_discoverer_end)

    def __len__(self):
        return len(self.__history)

    def __getitem__(self, item):
        return self.__history[item]

    def get_current(self):
        return self.__current_id

    def set_current(self, history_id):
        self.__current_id = history_id
        self.__changing_track_list = True
        self.__app.queue.open_files(self.__history[history_id]["list"])
        self.emit("change_current", history_id)

    def up_history(self, history_id):
        self.__history = self.__history[0:history_id] + self.__history[history_id + 1:] + [self.__history[history_id]]
        if self.__current_id == history_id:
            self.__current_id = len(self.__history)
        elif self.__current_id > history_id:
            self.__current_id -= 1
        self.emit("change_current", self.__current_id)

    def clear(self):
        self.__history = []
        self.__current_id = -1
        self.emit("clear")
        self.emit("change_current", self.__current_id)

    def __on_update(self, queue, was_cleared):
        identity = self.__identify_list(queue.get_unshuffled_tracks())

        if (was_cleared and not self.__changing_track_list) or not len(self.__history):
            self.__history.append(identity)
            self.__current_id = len(self.__history) - 1
            self.emit("append")
            self.emit("change_current", self.__current_id)
        else:
            self.__history[self.__current_id] = identity

        self.__changing_track_list = False

    def __on_discoverer_end(self, discoverer):
        if self.__current_id < 0:
            return

        identity = self.__identify_list(self.__app.queue.get_unshuffled_tracks())
        self.__history[self.__current_id] = identity

    @staticmethod
    def __identify_list(tracks):
        artists = set()
        unknown = 0

        for track in tracks:
            if track.info:
                artists.add(track.info.artist)
            else:
                unknown += 1

        return {
            "artists": list(artists),
            "unknown": unknown,
            "list": [track.fullpath for track in tracks]
        }
