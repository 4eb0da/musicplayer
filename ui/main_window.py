from gi.repository import Gtk

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='FileOpen' accel='<Primary>O'/>
      <separator />
      <menuitem action='FileQuit' />
    </menu>
  </menubar>
</ui>
"""

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.Window.__init__(self, title="MusicPlayer", application=app)
        self.app = app

        self.set_default_size(350, 200)

        action_group = Gtk.ActionGroup("actions")

        self.add_file_menu_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(menubar, False, False, 0)

        self.add(box)

    def add_file_menu_actions(self, action_group):
        action_group.add_actions([
            ("FileMenu", None, "File"),
            ("FileOpen", Gtk.STOCK_OPEN, None, None, None,
             self.on_open),
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

    def on_open(self, widget):
        pass

    def on_menu_file_quit(self, widget):
        self.app.quit()