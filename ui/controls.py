from gi.repository import Gtk


class Controls(Gtk.Toolbar):
    def __init__(self, app):
        Gtk.Toolbar.__init__(self)

        self.app = app

        self.set_hexpand(True)
        # self.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

        self.insert_spacer()
        self.previous = self.create_tool_button(Gtk.STOCK_MEDIA_PREVIOUS, "Previous")
        self.play = self.create_tool_button(Gtk.STOCK_MEDIA_PLAY, "Play")
        self.next = self.create_tool_button(Gtk.STOCK_MEDIA_NEXT, "Next")
        self.insert_spacer()

        self.previous.connect("clicked", lambda button: self.app.queue.previous())
        self.play.connect("clicked", self.on_play)
        self.next.connect("clicked", lambda button: self.app.queue.next())

        app.queue.connect("track", self.on_track)

    def insert_spacer(self):
        separator = Gtk.SeparatorToolItem.new()
        separator.set_draw(False)
        self.insert(separator, -1)
        self.child_set_property(separator, "expand", True)

    def create_tool_button(self, stock_id, tooltip):
        button = Gtk.ToolButton.new_from_stock(stock_id)
        button.set_tooltip_text(tooltip)
        button.set_sensitive(False)
        self.insert(button, -1)
        return button

    def on_play(self, button):
        self.app.queue.play_pause()
        self.toggle_button(self.app.queue.is_paused())

    def toggle_button(self, is_paused):
        if is_paused:
            self.play.set_stock_id(Gtk.STOCK_MEDIA_PLAY)
            self.play.set_tooltip_text("Play")
        else:
            self.play.set_stock_id(Gtk.STOCK_MEDIA_PAUSE)
            self.play.set_tooltip_text("Pause")

    def on_track(self, queue, track):
        has_track = bool(track)
        self.previous.set_sensitive(has_track)
        self.play.set_sensitive(has_track)
        self.next.set_sensitive(has_track)
        self.toggle_button(not has_track)
