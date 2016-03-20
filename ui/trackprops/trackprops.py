from gi.repository import Gtk, Gio, GObject
from urllib.request import pathname2url
from ui.util.formatters import duration
import os


class TrackProps(GObject.Object):
    __gsignals__ = {
        'change': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, tracks, selected):
        GObject.Object.__init__(self)

        self.tracks = tracks
        self.selected = None
        self.selected_index = selected

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackprops.glade"))

        if len(tracks) == 1:
            self.builder.get_object("prev").set_sensitive(False)
            self.builder.get_object("next").set_sensitive(False)

        self.dialog = self.builder.get_object("dialog1")

        self.builder.connect_signals(self)
        self.select_track(selected)

    def run(self):
        self.dialog.run()
        self.dialog.hide()

    def on_close_clicked(self, button):
        self.dialog.response(Gtk.ResponseType.CLOSE)

    def on_open_clicked(self, button):
        Gio.AppInfo.launch_default_for_uri('file:///' + pathname2url(os.path.dirname(self.selected.fullpath)), None)

    def on_prev_clicked(self, button):
        index = self.selected_index - 1
        if index < 0:
            index = len(self.tracks) - 1
        self.select_track(index)

    def on_next_clicked(self, button):
        index = self.selected_index + 1
        if index >= len(self.tracks):
            index = 0
        self.select_track(index)

    def select_track(self, index):
        self.selected = self.tracks[index]
        self.selected_index = index

        self.dialog.set_title("{} [{}/{}]".format(self.selected.info.title, index + 1, len(self.tracks)))

        self.builder.get_object("title").set_text(self.selected.info.title)
        self.builder.get_object("artist").set_text(self.selected.info.artist)
        self.builder.get_object("album").set_text(self.selected.info.album)
        self.builder.get_object("year").set_text(self.selected.info.year)
        self.builder.get_object("number").set_text(str(self.selected.info.number))
        self.builder.get_object("genre").set_text(self.selected.info.genre)
        self.builder.get_object("album_artist").set_text(self.selected.info.album_artist)
        self.builder.get_object("composer").set_text(self.selected.info.composer)
        self.builder.get_object("author").set_text(self.selected.info.author)
        self.builder.get_object("url").set_text(self.selected.info.url)
        self.builder.get_object("comment").get_buffer().set_text(self.selected.info.comment)


        self.builder.get_object("filename").set_text(self.selected.filename)
        self.builder.get_object("file_size").set_text("{:.2f} MB".format(os.stat(self.selected.fullpath).st_size / 1024 / 1024))
        self.builder.get_object("duration").set_text(duration(self.selected.info.audio["duration"]))
        self.builder.get_object("channels").set_text(str(self.selected.info.audio["channels"]))
        self.builder.get_object("bitrate").set_text(str(self.selected.info.audio["bitrate"]) + " kbps")

        self.emit("change", self.selected)
