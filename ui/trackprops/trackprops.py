from gi.repository import Gtk, Gio, GObject
from urllib.request import pathname2url
from ui.util.formatters import duration
from threading import Thread
import os
import time


class TrackProps(GObject.Object):
    __gsignals__ = {
        'change': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, app, tracks, selected):
        GObject.Object.__init__(self)

        self.app = app
        self.tracks = tracks
        self.selected = None
        self.selected_index = selected
        self.synced_fields = []
        self.saved_map = {}
        self.destroyed = False
        self.missing_infos = set()

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackprops.glade"))

        if len(tracks) == 1:
            self.builder.get_object("prev").set_sensitive(False)
            self.builder.get_object("next").set_sensitive(False)

        empty_tracks = set()
        for track in tracks:
            if not track.info:
                empty_tracks.add(track)

        if empty_tracks:
            handler_id = None
            indicator = self.builder.get_object("indicator")

            def update(discoverer, updated):
                for track in updated:
                    if track in empty_tracks:
                        empty_tracks.remove(track)
                        if self.selected == track:
                            self.update_selected_track()
                    if track in self.missing_infos:
                        self.missing_infos.remove(track)
                        if not self.missing_infos:
                            self.save()

                if not empty_tracks:
                    app.discoverer.disconnect(handler_id)
                    indicator.hide()
                    self.init_synced_fields()

            handler_id = app.discoverer.connect("info", update)
            indicator.show()

        self.dialog = self.builder.get_object("dialog1")

        self.builder.connect_signals(self)
        self.init_synced_fields()
        self.bind_change_events()
        self.select_track(selected)

    def run(self):
        self.dialog.run()

    def destroy(self):
        self.destroyed = True
        self.dialog.destroy()

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

    def get_track_attr(self, field, track=None):
        if track is None:
            track = self.selected

        if track in self.saved_map and field in self.saved_map[track]:
            return self.saved_map[track][field]
        if not track.info:
            return ""

        return getattr(track.info, field)

    def select_track(self, index):
        self.selected = self.tracks[index]
        self.selected_index = index
        self.update_selected_track()

    def update_selected_track(self):
        self.dialog.set_title("{} [{}/{}]".format(self.get_track_attr("title") or "Unknown", self.selected_index + 1, len(self.tracks)))

        self.builder.get_object("title").set_text(self.get_track_attr("title"))
        self.builder.get_object("number").set_text(str(self.get_track_attr("number")))
        self.builder.get_object("comment").get_buffer().set_text(self.get_track_attr('comment'))
        for field in self.synced_fields:
            self.builder.get_object(field).set_text(self.get_track_attr(field))

        self.builder.get_object("filename").set_text(self.selected.filename)
        self.builder.get_object("file_size").set_text("{:.2f} MB".format(os.stat(self.selected.fullpath).st_size / 1024 / 1024))

        if self.selected.info:
            self.builder.get_object("duration").set_text(duration(self.selected.info.audio["duration"]))
            self.builder.get_object("channels").set_text(str(self.selected.info.audio["channels"]))
            self.builder.get_object("bitrate").set_text(str(self.selected.info.audio["bitrate"]) + " kbps")
        else:
            self.builder.get_object("duration").set_text("")
            self.builder.get_object("channels").set_text("")
            self.builder.get_object("bitrate").set_text("")

        self.emit("change", self.selected)

    def init_synced_fields(self):
        self.init_synced_field("artist")
        self.init_synced_field("album")
        self.init_synced_field("year")
        self.init_synced_field("genre")
        self.init_synced_field("album_artist")
        self.init_synced_field("album_artist")
        self.init_synced_field("composer")
        self.init_synced_field("author")
        self.init_synced_field("url")

    def init_synced_field(self, field_name):
        vals = set()
        for track in self.tracks:
            if track.info:
                vals.add(getattr(track.info, field_name))
        model = Gtk.ListStore(str)
        for field in vals:
            model.append([field])
        completion = Gtk.EntryCompletion.new()
        completion.set_model(model)
        completion.set_text_column(0)

        self.builder.get_object(field_name).set_completion(completion)
        sync_button = self.builder.get_object(field_name + "_sync")
        sync_button.set_data("field", field_name)
        sync_button.connect("clicked", self.on_sync)

        if len(vals) > 1:
            sync_button.set_sensitive(True)

        self.synced_fields.append(field_name)

    def on_sync(self, button):
        button.set_sensitive(False)
        field_name = button.get_data("field")
        val = self.get_track_attr(field_name)
        for track in self.tracks:
            if self.get_track_attr(field_name, track) is not val:
                self.save_to_map(track, field_name, val)

    def bind_change_events(self):
        fields = self.synced_fields + ["title", "number", "comment"]
        for field in fields:
            entry = self.builder.get_object(field)
            entry.set_data("field", field)
            entry.connect("focus-out-event", self.on_entry_blur)

    def on_entry_blur(self, entry, event):
        field = entry.get_data("field")
        prev_val = self.get_track_attr(field)
        new_val = ""
        if hasattr(entry, "get_text"):
            new_val = entry.get_text()
        else:
            buffer = entry.get_buffer()
            start, end = buffer.get_bounds()
            new_val = buffer.get_text(start, end, True)
        if prev_val != new_val:
            self.save_to_map(self.selected, field, new_val)
            unique_vals = set()
            for track in self.tracks:
                unique_vals.add(self.get_track_attr(field, track))
            sync_button = self.builder.get_object(field + "_sync")
            if sync_button:
                sync_button.set_sensitive(len(unique_vals) > 1)

    def save_to_map(self, track, field, val):
        if track not in self.saved_map:
            self.saved_map[track] = {}

        self.saved_map[track][field] = val

    def on_save_clicked(self, button):
        self.dialog.set_modal(True)

        count = len(self.saved_map)

        if count == 0:
            self.dialog.response(Gtk.ResponseType.APPLY)
            return

        progressbar = self.builder.get_object("progress")
        progressbar.set_show_text(True)
        progressbar.show()
        self.disable_all()

        self.missing_infos = set([track for track in self.saved_map if not track.info])
        if self.missing_infos:
            progressbar.set_text("Waiting for track info")
        else:
            self.save()

    def disable_all(self):
        fields = [
            "title",
            "artist",
            "album",
            "year",
            "number",
            "genre",
            "album_artist",
            "composer",
            "author",
            "url",
            "comment",
            "artist_sync",
            "album_sync",
            "year_sync",
            "genre_sync",
            "album_artist_sync",
            "composer_sync",
            "author_sync",
            "url_sync",
            "prev",
            "next",
            "save"
        ]

        for field in fields:
            self.builder.get_object(field).set_sensitive(False)

    def save(self):
        progressbar = self.builder.get_object("progress")
        count = len(self.saved_map)

        def update_progressbar(done):
            progressbar.set_text("{} / {}".format(done, count))
            progressbar.set_fraction(done / count)

        def thread_run(discoverer, saved_map):
            for index, track in enumerate(saved_map):
                if self.destroyed:
                    return

                discoverer.save_tags(track, saved_map[track])
                GObject.idle_add(update_progressbar, index)

                if (index + 1) % 20 == 0:
                    time.sleep(0.01)
            GObject.idle_add(thread_done,)

        def thread_done():
            self.dialog.response(Gtk.ResponseType.APPLY)

        update_progressbar(0)
        thread = Thread(target=thread_run, args=(self.app.discoverer, self.saved_map,))
        thread.start()
