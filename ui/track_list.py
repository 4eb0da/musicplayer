from gi.repository import Gtk, GObject, Pango


class TrackList(Gtk.ScrolledWindow):
    def __init__(self, app):
        Gtk.ScrolledWindow.__init__(self)
        self.app = app
        self.track_to_iter = {}
        self.reorder_insert_position = None
        self.store = Gtk.ListStore(str, object)
        self.store.connect("row-inserted", self.on_reorder_insert)
        self.store.connect("row-deleted", self.on_reorder_delete)
        self.list_view = Gtk.TreeView(model=self.store)
        self.list_view.set_reorderable(True)
        self.list_view.set_headers_visible(False)
        self.list_view.set_vscroll_policy(Gtk.ScrollablePolicy.MINIMUM)
        selection = self.list_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.list_view.connect("row_activated", self.on_track_activate)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.list_view.append_column(column)

        self.add(self.list_view)

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
        if track:
            self.list_view.set_cursor(self.store.get_path(self.track_to_iter[track]))

    def on_track_activate(self, view, path, column):
        track = self.store[self.store.get_iter(path)][1]
        self.app.queue.set_current(track)

    def on_file_update(self, discoverer, track):
        if track in self.track_to_iter:
            self.store[self.track_to_iter[track]] = [track.name(), track]

    def on_reorder_insert(self, model, path, iter):
        self.reorder_insert_position = int(str(path))

    def on_reorder_delete(self, model, path):
        index = int(str(path))
        if self.reorder_insert_position is not None and abs(index - self.reorder_insert_position) > 1:
            if index > self.reorder_insert_position:
                index -= 1
            else:
                self.reorder_insert_position -= 1
            self.app.queue.reoder(index, self.reorder_insert_position)
            # prevent error at the last pos
            GObject.idle_add(self.list_view.set_cursor, Gtk.TreePath.new_from_string(str(self.reorder_insert_position)))
            self.reorder_insert_position = None
