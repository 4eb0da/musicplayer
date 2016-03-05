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

        action_group = Gtk.ActionGroup("actions")
        self.add_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        self.popup = uimanager.get_widget("/PopupMenu")

        self.store = Gtk.ListStore(str, object)
        self.store.connect("row-inserted", self.on_reorder_insert)
        self.store.connect("row-deleted", self.on_reorder_delete)

        self.list_view = Gtk.TreeView(model=self.store)
        self.list_view.set_reorderable(True)
        self.list_view.set_headers_visible(False)
        self.list_view.set_vscroll_policy(Gtk.ScrollablePolicy.MINIMUM)
        # selection = self.list_view.get_selection()
        # selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.list_view.connect("row_activated", self.on_track_activate)
        self.list_view.connect("button-press-event", self.on_mouse_click)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.list_view.append_column(column)

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

    def on_queue_update(self, queue, list):
        self.store.clear()
        self.track_to_path.clear()
        for track in list:
            self.track_to_path[track] = self.store.get_path(self.store.append([track.name(), track]))
        self.list_view.set_model(self.store)

    def on_track_change(self, queue, track):
        if track:
            self.list_view.set_cursor(self.track_to_path[track])

    def on_track_activate(self, view, path, column):
        track = self.store[self.store.get_iter(path)][1]
        self.app.queue.set_current(track)

    def on_file_update(self, discoverer, track):
        if track in self.track_to_path:
            self.store[self.store.get_iter(self.track_to_path[track])] = [track.name(), track]

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

    def on_remove_from_list(self, action):
        self.removing = True
        model, iter = self.list_view.get_selection().get_selected()
        pos = int(str(self.store.get_path(iter)))
        self.app.queue.remove(pos)
        self.store.remove(iter)
        self.update_paths()
        self.removing = False
