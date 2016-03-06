from gi.repository import Gtk, Gdk, GObject


class Tools(Gtk.Toolbar):
    __gsignals__ = {
        'equalizer_toggle': (GObject.SIGNAL_RUN_FIRST, None, (bool,))
    }

    def __init__(self, app):
        Gtk.Toolbar.__init__(self)

        self.app = app

        self.set_hexpand(True)
        style_context = self.get_style_context()
        style_context.add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR)

        css_provider = Gtk.CssProvider()
        toolbar_css = ".inline-toolbar.toolbar { border-color: transparent; }"
        css_provider.load_from_data(toolbar_css.encode('UTF-8'))
        screen = Gdk.Screen.get_default()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.insert_spacer()
        self.equalizer = self.create_tool_button("preferences-desktop-multimedia", "Equalizer")

        self.equalizer.connect("clicked", self.toggle_equalizer)

    def insert_spacer(self):
        separator = Gtk.SeparatorToolItem.new()
        separator.set_draw(False)
        self.insert(separator, -1)
        self.child_set_property(separator, "expand", True)

    def create_tool_button(self, icon, tooltip):
        button = Gtk.ToggleToolButton.new()
        button.set_tooltip_text(tooltip)
        button.set_icon_name(icon)
        self.insert(button, -1)
        return button

    def toggle_equalizer(self, button):
        self.emit("equalizer-toggle", button.get_active())
