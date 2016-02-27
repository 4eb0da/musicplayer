from gi.repository import Gtk, GObject, Pango

class TrackList(Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.track_to_iter = {}
        self.store = Gtk.ListStore(str, object)
        self.list_view = Gtk.TreeView(model=self.store)
        self.list_view.set_reorderable(True)
        self.list_view.set_headers_visible(False)
        self.list_view.connect("row_activated", self.on_track_activate)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.list_view.append_column(column)

        self.pack_start(self.list_view, False, False, 0)

        app.queue.connect("update", self.on_queue_update)
        app.queue.connect("track", self.on_track_change)
        app.discoverer.connect("info", self.on_file_update)

    def on_queue_update(self, queue, list):
        self.store.clear()
        self.track_to_iter.clear()
        for track in list:
            self.track_to_iter[track] = self.store.append([track.name(), track])
        self.list_view.set_model(self.store)

    def on_track_change(self, queue, track):
        self.list_view.set_cursor(self.store.get_path(self.track_to_iter[track]))

    def on_track_activate(self, view, path, column):
        track = self.store[self.store.get_iter(path)][1]
        self.app.queue.set_current(track)

    def on_file_update(self, discoverer, track):
        if track in self.track_to_iter:
            self.store[self.track_to_iter[track]] = [track.name(), track]
