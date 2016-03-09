from gi.repository import Gtk, Gdk, GObject, Pango

UI_INFO = """
<ui>
  <popup name='PopupMenu'>
    <menuitem action='RemoveFromList' />
  </popup>
</ui>
"""


class TrackList(Gtk.ScrolledWindow):
    def __init__(self, app):
        Gtk.ScrolledWindow.__init__(self)
        self.app = app
        self.track_to_path = {}
        self.reorder_insert_position = None
        self.removing = False
        self.prev_playing_track = None

        action_group = Gtk.ActionGroup("actions")
        self.add_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        self.popup = uimanager.get_widget("/PopupMenu")

        self.store = Gtk.ListStore(object, bool)
        self.store.connect("row-inserted", self.on_reorder_insert)
        self.store.connect("row-deleted", self.on_reorder_delete)

        self.list_view = Gtk.TreeView(model=self.store)
        self.list_view.set_reorderable(True)
        self.list_view.set_headers_visible(False)
        self.list_view.set_vscroll_policy(Gtk.ScrollablePolicy.MINIMUM)
        selection = self.list_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.list_view.connect("row-activated", self.on_track_activate)
        self.list_view.connect("button-press-event", self.on_mouse_click)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn("Now playing", renderer_pixbuf)
        column_pixbuf.set_cell_data_func(renderer_pixbuf, self.icon_renderer)
        self.list_view.append_column(column_pixbuf)

        renderer_title = Gtk.CellRendererText()
        renderer_title.set_property("ellipsize", Pango.EllipsizeMode.END)
        column_title = Gtk.TreeViewColumn("Title", renderer_title)
        column_title.set_cell_data_func(renderer_title, self.title_renderer)

        self.list_view.append_column(column_title)

        self.add(self.list_view)

        app.queue.connect("update", self.on_queue_update)
        app.queue.connect("track", self.on_track_change)
        app.discoverer.connect("info", self.on_file_update)

    def add_actions(self, action_group):
        action_group.add_actions([
            ("RemoveFromList", None, "Remove from list", None, None, self.on_remove_from_list)
        ])

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        return uimanager

    def icon_renderer(self, tree_column, cell, tree_model, iter, data):
        icon = None
        if tree_model[iter][1]:
            icon = "media-playback-start-symbolic"
        cell.set_property("icon-name", icon)

    def title_renderer(self, tree_column, cell, tree_model, iter, data):
        cell.set_property("text", tree_model[iter][0].name())

    def on_queue_update(self, queue, tracks):
        self.store.clear()
        self.track_to_path.clear()
        if self.prev_playing_track not in tracks:
            self.prev_playing_track = None
        for track in tracks:
            self.track_to_path[track] = self.store.get_path(self.store.append([track, track is self.prev_playing_track]))
        self.list_view.set_model(self.store)

    def on_track_change(self, queue, track):
        if track:
            self.list_view.set_cursor(self.track_to_path[track])
            if self.prev_playing_track is not None:
                self.store[self.store.get_iter(self.track_to_path[self.prev_playing_track])][1] = False
            self.store[self.store.get_iter(self.track_to_path[track])][1] = True
            self.prev_playing_track = track

    def on_track_activate(self, view, path, column):
        track = self.store[self.store.get_iter(path)][0]
        self.app.queue.set_current(track)

    def on_file_update(self, discoverer, track):
        if track in self.track_to_path:
            self.store[self.store.get_iter(self.track_to_path[track])][0] = track

    def on_reorder_insert(self, model, path, iter):
        self.reorder_insert_position = int(str(path))

    def on_reorder_delete(self, model, path):
        if self.removing:
            return

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

            self.update_paths()

    def update_paths(self):
        for index, row in enumerate(self.store):
            self.track_to_path[row[1]] = Gtk.TreePath.new_from_string(str(index))

    def on_mouse_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            # if right click activate a pop-up menu

            selection = self.list_view.get_selection()
            # store, list = selection.get_selected_rows()
            if selection.count_selected_rows():
                self.popup.popup(None, None, None, None, event.button, event.time)
            else:
                selection.unselect_all()

            return True

    def on_remove_from_list(self, action):
        self.removing = True
        store, list = self.list_view.get_selection().get_selected_rows()
        indices = [int(str(path)) for path in list]
        self.app.queue.remove(indices)
        self.removing = False
