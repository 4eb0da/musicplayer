from gi.repository import Gtk, Gdk, GObject, Pango
from .util import keyboard
from .trackprops.trackprops import TrackProps

UI_INFO = """
<ui>
  <popup name='PopupMenu'>
    <menuitem action='RemoveFromList' />
    <menuitem action='Properties' />
  </popup>
</ui>
"""


class TrackList(Gtk.ScrolledWindow):
    __gsignals__ = {
        'insert': (GObject.SIGNAL_RUN_FIRST, None, (object, int,))
    }

    def __init__(self, app):
        Gtk.ScrolledWindow.__init__(self)
        self.app = app
        self.tracks = []
        self.track_to_path = {}
        self.prev_playing_track = None
        self.drag_start_x = None
        self.drag_start_y = None
        self.drag_insert_pos = None
        self.motion_handler = None
        self.release_handler = None
        self.drag_start_win = None
        self.press_event_copy = None

        action_group = Gtk.ActionGroup("actions")
        self.add_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        self.popup = uimanager.get_widget("/PopupMenu")

        # track, is_playing, search_text
        self.store = Gtk.ListStore(object, bool, str)

        self.list_view = Gtk.TreeView(model=self.store)
        self.list_view.set_headers_visible(False)
        self.list_view.set_vscroll_policy(Gtk.ScrollablePolicy.MINIMUM)
        selection = self.list_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.list_view.drag_dest_set(0, None, 0)
        self.list_view.connect("row-activated", self.on_track_activate)
        self.list_view.connect("button-press-event", self.on_mouse_click)
        self.list_view.connect("popup-menu", self.on_popup_menu)
        self.list_view.connect("drag-motion", self.on_drag_motion)
        self.list_view.connect("drag-drop", self.on_drag_drop)
        self.list_view.connect("drag-data-received", self.on_drag_drop_data)

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
            ("RemoveFromList", None, "Remove from list", None, None, self.on_remove_from_list),
            ("Properties", None, "Properties", None, None, self.on_properties)
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
        self.tracks = tracks
        if self.prev_playing_track not in tracks:
            self.prev_playing_track = None
        for track in tracks:
            self.track_to_path[track] = self.store.get_path(
                self.store.append([track, track is self.prev_playing_track, track.name()]))
        self.list_view.set_model(self.store)
        self.list_view.set_search_column(2)

    def on_track_change(self, queue, track):
        if track:
            self.list_view.set_cursor(self.track_to_path[track])
            if self.prev_playing_track is not None:
                self.store[self.store.get_iter(self.track_to_path[self.prev_playing_track])][1] = False
            iter = self.store.get_iter(self.track_to_path[track])
            self.store[iter][1] = True
            self.store[iter][2] = track.name()
            self.prev_playing_track = track

    def on_track_activate(self, view, path, column):
        track = self.store[self.store.get_iter(path)][0]
        self.app.queue.set_current(track)

    def on_file_update(self, discoverer, pack):
        for track in pack:
            if track in self.track_to_path:
                path = self.track_to_path[track]
                iter = self.store.get_iter(path)
                self.store[iter][0] = track
                self.store[iter][2] = track.name()

    def update_paths(self):
        for index, row in enumerate(self.store):
            self.track_to_path[row[1]] = Gtk.TreePath.new_from_string(str(index))

    def on_mouse_click(self, widget, event):
        if len(self.store) == 0:
            return

        # it can be Gdk.EventType.2BUTTON_PRESS
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == Gdk.BUTTON_SECONDARY:
                # if right click activate a pop-up menu
                selection = self.list_view.get_selection()
                path, column, cell_x, cell_y = self.list_view.get_path_at_pos(event.x, event.y)
                if not selection.path_is_selected(path):
                    selection.unselect_all()
                    selection.select_path(path)
                # store, list = selection.get_selected_rows()
                if selection.count_selected_rows():
                    self.popup.popup(None, None, None, None, event.button, event.time)

                return True
            elif event.button == Gdk.BUTTON_PRIMARY:
                path, column, cell_x, cell_y = self.list_view.get_path_at_pos(event.x, event.y)
                selection = self.list_view.get_selection()
                has_modifier = event.state & Gdk.ModifierType.CONTROL_MASK or event.state & Gdk.ModifierType.SHIFT_MASK
                if has_modifier:
                    # if Gtk.TreeView has no focus, default handler will not select row
                    self.list_view.grab_focus()
                    return False

                # have no idea how to check it properly - propagate_event changes event
                if self.press_event_copy and event.get_time() == self.press_event_copy.get_time():
                    return False
                if not selection.path_is_selected(path):
                    if not has_modifier:
                        selection.unselect_all()
                    selection.select_path(path)
                self.drag_start_x = event.x
                self.drag_start_y = event.y

                # copy event for proper double click work - if it's propagated, ignore it
                self.clear_event_copy()
                self.press_event_copy = event.copy()

                self.motion_handler = self.list_view.connect("motion-notify-event", self.on_mouse_move)
                self.release_handler = self.list_view.connect("button-release-event", self.on_mouse_release)
                return True

    def on_popup_menu(self, widget):
        selection = self.list_view.get_selection()
        if selection.count_selected_rows() > 0:
            self.popup.popup(None, None, None, None, Gdk.BUTTON_SECONDARY, Gtk.get_current_event_time())

    def on_mouse_move(self, widget, event):
        if self.drag_check_threshold(self.drag_start_x, self.drag_start_y, event.x, event.y):
            context = self.list_view.drag_begin(Gtk.TargetList.new([]), Gdk.DragAction.MOVE, 1, event)
            self.drag_start_win = context.get_source_window()
            self.stop_watch_move()
            self.clear_event_copy()

    def on_mouse_release(self, widget, event):
        self.stop_watch_move()
        if self.press_event_copy:
            Gtk.propagate_event(widget, self.press_event_copy)
            self.clear_event_copy()

    def clear_event_copy(self):
        if self.press_event_copy:
            # some strange error here - mb pygtk clears it somewhere?
            # self.press_event_copy.free()
            self.press_event_copy = None

    def stop_watch_move(self):
        if self.motion_handler is not None:
            self.list_view.disconnect(self.motion_handler)
            self.motion_handler = None
        if self.release_handler is not None:
            self.list_view.disconnect(self.release_handler)
            self.release_handler = None

    def fix_drag_pos(self, pos):
        if pos is Gtk.TreeViewDropPosition.INTO_OR_BEFORE:
            pos = Gtk.TreeViewDropPosition.BEFORE
        elif pos is Gtk.TreeViewDropPosition.INTO_OR_AFTER:
            pos = Gtk.TreeViewDropPosition.AFTER

        return pos

    def is_external_add(self):
        mask = keyboard.get_mask(self)
        return mask & Gdk.ModifierType.CONTROL_MASK and len(self.store) > 0

    def on_drag_motion(self, widget, context, x, y, time):
        is_self_source = context.get_source_window() is self.drag_start_win
        is_external_add = self.is_external_add()
        # if reorder or append
        if is_self_source or is_external_add:
            path, pos = self.list_view.get_dest_row_at_pos(x, y)
            pos = self.fix_drag_pos(pos)

            self.list_view.set_drag_dest_row(path, pos)
            Gdk.drag_status(context, Gdk.DragAction.COPY if is_external_add else Gdk.DragAction.MOVE, time)
            return True

    def on_drag_drop(self, widget, context, x, y, time):
        is_self_source = context.get_source_window() is self.drag_start_win
        is_external_add = self.is_external_add()
        # if reorder or append
        if is_self_source or is_external_add:
            path, pos = self.list_view.get_dest_row_at_pos(x, y)
            pos = self.fix_drag_pos(pos)
            insert_pos = int(str(path)) + (1 if pos is Gtk.TreeViewDropPosition.AFTER else 0)

            if is_self_source:
                selection = self.list_view.get_selection()
                store, list = selection.get_selected_rows()

                result_pos = self.app.queue.reoder([int(str(path)) for path in list], insert_pos)

                # select reordered rows
                for i in range(len(list)):
                    path = Gtk.TreePath.new_from_string(str(i + result_pos))
                    selection.select_path(path)

                Gtk.drag_finish(context, True, True, time)
            else:
                targets = [target for target in context.list_targets() if target.name() == 'text/uri-list']
                if len(targets) == 0:
                    return False
                self.drag_insert_pos = insert_pos
                self.list_view.drag_get_data(context, targets[0], time)

            return True

    def on_drag_drop_data(self, widget, context, x, y, data, info, time):
        self.emit("insert", data, self.drag_insert_pos)

    def on_remove_from_list(self, action):
        store, list = self.list_view.get_selection().get_selected_rows()
        indices = [int(str(path)) for path in list]
        self.app.queue.remove(indices)

    def on_properties(self, action):
        store, list = self.list_view.get_selection().get_selected_rows()
        tracks = [self.store[self.store.get_iter(path)][0] for path in list]
        index = 0

        if len(tracks) == 1:
            tracks = self.tracks
            index = int(str(list[0]))

        def show_dialog():
            props = TrackProps(self.app, tracks, index)
            props.connect("change", lambda props, track: self.list_view.set_cursor(self.track_to_path[track]))
            props.run()
            props.destroy()

        GObject.idle_add(show_dialog)

