from gi.repository import Gtk, Gdk, GObject

from .components.MenuToolButton import MenuToolButton

UI_INFO = """
<ui>
  <popup name='PopupMenu'>
    <menuitem action='AddFilesToList' />
    <menuitem action='AddDirToList' />
  </popup>
</ui>
"""


class Tools(Gtk.Toolbar):
    __gsignals__ = {
        'repeat_toggle': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'shuffle_toggle': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'equalizer_toggle': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'add_files': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'add_dir': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, app):
        Gtk.Toolbar.__init__(self)

        self.app = app

        action_group = Gtk.ActionGroup("actions")
        self.add_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        playlist_popup = uimanager.get_widget("/PopupMenu")

        self.set_hexpand(True)
        style_context = self.get_style_context()
        style_context.add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR)

        css_provider = Gtk.CssProvider()
        toolbar_css = ".inline-toolbar.toolbar { border-color: transparent; }"
        css_provider.load_from_data(toolbar_css.encode('UTF-8'))
        screen = Gdk.Screen.get_default()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.insert_spacer()

        self.create_tool_button("gtk-justify-fill", "Playlist", playlist_popup)

        self.repeat = self.create_tool_button("media-playlist-repeat", "Repeat")
        self.repeat.set_active(app.queue.repeat)
        self.repeat.connect("clicked", lambda button: self.emit("repeat-toggle", button.get_active()))

        self.shuffle = self.create_tool_button("media-playlist-shuffle", "Shuffle")
        self.shuffle.set_active(app.queue.shuffle)
        self.shuffle.connect("clicked", lambda button: self.emit("shuffle-toggle", button.get_active()))

        self.equalizer = self.create_tool_button("preferences-desktop-multimedia", "Equalizer")
        self.equalizer.set_active(app.settings.getboolean("ui", "tools.equalizer", False))
        self.equalizer.connect("clicked", self.emit_equalizer)

    def add_actions(self, action_group):
        action_group.add_actions([
            ("AddFilesToList", None, "Add files to list", None, None, lambda action: self.emit("add_files")),
            ("AddDirToList", None, "Add directory to list", None, None, lambda action: self.emit("add_dir"))
        ])

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        return uimanager

    def insert_spacer(self):
        separator = Gtk.SeparatorToolItem.new()
        separator.set_draw(False)
        self.insert(separator, -1)
        self.child_set_property(separator, "expand", True)

    def create_tool_button(self, icon, tooltip, popup=None):
        button = MenuToolButton(popup) if popup else Gtk.ToggleToolButton.new()
        button.set_tooltip_text(tooltip)
        button.set_icon_name(icon)
        self.insert(button, -1)
        return button

    def emit_equalizer(self, button):
        is_active = button.get_active()
        self.emit("equalizer-toggle", is_active)
        self.app.settings.setboolean("ui", "tools.equalizer", is_active)
