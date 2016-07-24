from gi.repository import Unity, Dbusmenu


class UnityQuickList:
    DESKTOP_ENTRY = "musicplayer.desktop"

    def __init__(self, app):
        launcher = Unity.LauncherEntry.get_for_desktop_id(self.DESKTOP_ENTRY)

        self.__play = Dbusmenu.Menuitem.new()
        self.__play.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Play")
        self.__play.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, False)
        self.__play.connect("item-activated", lambda item, ts: app.queue.play_pause())

        self.__previous = Dbusmenu.Menuitem.new()
        self.__previous.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Previous")
        self.__previous.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, False)
        self.__previous.connect("item-activated", lambda item, ts: app.queue.previous())

        self.__next = Dbusmenu.Menuitem.new()
        self.__next.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Next")
        self.__next.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, False)
        self.__next.connect("item-activated", lambda item, ts: app.queue.next())

        quick_list = Dbusmenu.Menuitem.new()
        quick_list.child_append(self.__play)
        quick_list.child_append(self.__previous)
        quick_list.child_append(self.__next)

        launcher.set_property("quicklist", quick_list)

        app.queue.connect("track", self.__on_track)
        app.queue.connect("play_pause", self.__play_pause)

    def __on_track(self, queue, track):
        if track:
            for item in [self.__play, self.__previous, self.__next]:
                item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)

    def __play_pause(self, queue, play):
        self.__play.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Pause" if play else "Play")
