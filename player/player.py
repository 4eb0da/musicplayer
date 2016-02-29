from gi.repository import GObject, Gst, GdkPixbuf
import urllib.request, urllib.parse
from .track import Track


class Player(GObject.Object):
    __gsignals__ = {
        'play': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'eof': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'cover': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, app):
        GObject.Object.__init__(self)
        self.app = app

        self.__inited = False

    def play(self, track):
        self.emit('play', track)

        self.init_gst()
        self.open_file(track.fullpath)

    def init_gst(self):
        if self.__inited:
            return

        self.__inited = True

        # Create GStreamer pipeline
        self.pipeline = Gst.Pipeline()

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message)

        # Create GStreamer elements
        self.playbin = Gst.ElementFactory.make('playbin', None)

        # Add playbin to the pipeline
        self.pipeline.add(self.playbin)

    def open_file(self, fullpath):
        fileurl = urllib.parse.urljoin('file:', urllib.request.pathname2url(fullpath))

        self.pipeline.set_state(Gst.State.NULL)
        self.playbin.set_property('uri', fileurl)
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_message(self, bus, msg):
        struct = msg.get_structure()
        if msg.type == Gst.MessageType.EOS:
            self.emit("eof")
        elif msg.type == Gst.MessageType.TAG and msg.parse_tag() and struct.has_field('taglist'):
            taglist = struct.get_value('taglist')
            for x in range(taglist.n_tags()):
                name = taglist.nth_tag_name(x)
                if name == "preview-image" or name == "image":
                    success, sample = taglist.get_sample(name)
                    if success:
                        buffer = sample.get_buffer()
                        if buffer:
                            loader = GdkPixbuf.PixbufLoader()
                            data = buffer.extract_dup(0, buffer.get_size())
                            loader.write(data)
                            pixbuf = loader.get_pixbuf()
                            loader.close()
                            self.emit("cover", pixbuf)

    def get_position(self):
        return self.pipeline.query_position(Gst.Format.TIME)[1] / Gst.MSECOND

    def set_position(self, pos):
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, pos * Gst.MSECOND)

    def get_duration(self):
        return self.pipeline.query_duration(Gst.Format.TIME)[1] / Gst.MSECOND

    def resume(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def set_volume(self, volume):
        self.playbin.set_property("volume", volume)
