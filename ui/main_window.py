from urllib.parse import urlparse
from urllib.request import url2pathname

from gi.repository import Gtk, Gdk

from ui.controls import Controls
from ui.current_track import CurrentTrack
from ui.equalizer.equalizer import Equalizer
from ui.tools import Tools
from ui.track_list import TrackList
from .util import keyboard

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='FileOpen' accel='<Primary>O'/>
      <menuitem action='DirOpen' accel='<Primary><Shift>O'/>
      <separator />
      <menuitem action='FileQuit' accel='<Primary>Q'/>
    </menu>
  </menubar>
</ui>
"""


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.Window.__init__(self, title="MusicPlayer", application=app)
        self.app = app

        self.set_default_size(350, 500)

        action_group = Gtk.ActionGroup("actions")

        self.add_file_menu_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE)
        self.drag_dest_add_uri_targets()
        self.connect("drag-motion", self.on_drag_motion)
        self.connect("drag-data-received", self.on_drop)

        current_track = CurrentTrack(app)
        controls = Controls(app)
        track_list = TrackList(app)
        self.equalizer = Equalizer(app)
        tools = Tools(app)

        if app.settings.getboolean("ui", "tools.equalizer", False) is False:
            self.connect("show", lambda win: self.equalizer.hide())

        track_list.connect("insert", self.on_list_insert)
        tools.connect("equalizer-toggle", self.toggle_equalizer)
        tools.connect("repeat-toggle", lambda tools, toggle: app.queue.toggle_repeat(toggle))
        tools.connect("shuffle-toggle", lambda tools, toggle: app.queue.toggle_shuffle(toggle))
        tools.connect("add-files", lambda tools: self.open_files(directory=False, append=True))
        tools.connect("add-dir", lambda tools: self.open_files(directory=True, append=True))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(menubar, False, False, 0)
        box.pack_start(current_track, False, False, 0)
        box.pack_start(controls, False, False, 0)
        box.pack_start(track_list, True, True, 0)
        box.pack_start(self.equalizer, False, False, 0)
        box.pack_start(tools, False, False, 0)

        self.add(box)

    def add_file_menu_actions(self, action_group):
        action_group.add_actions([
            ("FileMenu", None, "File"),
            ("FileOpen", Gtk.STOCK_OPEN, None, None, None,
             self.on_open),
            ("DirOpen", None, "Open directory", "<Primary><Shift>O", None,
             self.on_open_dir),
            ("FileQuit", Gtk.STOCK_QUIT, None, None, None,
             self.on_menu_file_quit)
        ])

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def open_files(self, directory=False, append=False):
        dialog = Gtk.FileChooserDialog("Please choose a folder" if directory else "Choose an audio file", self,
            Gtk.FileChooserAction.SELECT_FOLDER if directory else Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        dialog.set_select_multiple(True)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            if append:
                self.app.queue.append_files(files)
            else:
                self.app.queue.open_files(files)

        dialog.destroy()

    def on_open(self, widget):
        self.open_files(directory=False, append=False)

    def on_open_dir(self, widget):
        self.open_files(directory=True, append=False)

    def on_menu_file_quit(self, widget):
        self.app.quit()

    def on_drag_motion(self, widget, context, x, y, time):
        mask = keyboard.get_mask(self)
        if mask & Gdk.ModifierType.CONTROL_MASK:
            Gdk.drag_status(context, Gdk.DragAction.COPY, time)
        else:
            Gdk.drag_status(context, Gdk.DragAction.MOVE, time)
        return True

    @staticmethod
    def drag_get_dirs(data):
        return [url2pathname(urlparse(p).path) for p in data.get_uris()]

    def on_list_insert(self, widget, data, insert_pos):
        paths = self.drag_get_dirs(data)
        self.app.queue.append_files(paths, insert_pos)

    def on_drop(self, widget, context, x, y, data, info, time):
        dirs = self.drag_get_dirs(data)
        if context.get_selected_action() is Gdk.DragAction.COPY:
            self.app.queue.append_files(dirs)
        else:
            self.app.queue.open_files(dirs)

    def toggle_equalizer(self, tools, toggle):
        if toggle:
            self.equalizer.show()
        else:
            self.equalizer.hide()
