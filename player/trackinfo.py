import re
import os


class TrackInfo:
    # russian letters encoding fix
    LETTERS = "абвгдеёжзийклмнопрстуфхцчшщьыъэюя"
    LETTERS += LETTERS.upper()
    LETTERS = LETTERS.encode("cp1251").decode("cp1252")

    @staticmethod
    def convert(fullpath, string):
        if fullpath.endswith(".mp3") and re.search("[" + TrackInfo.LETTERS + "]", string):
            try:
                return string.encode("cp1252").decode("cp1251")
            except:
                return string
        return string

    def __init__(self, fullpath, file_info):
        tags = file_info.tags

        def get(name):
            return name in tags and len(tags[name]) and tags[name][0] or ""

        self.title = self.convert(fullpath, get("TITLE")) or os.path.basename(fullpath)
        self.album = self.convert(fullpath, get("ALBUM") or "")
        self.artist = self.convert(fullpath, get("ARTIST") or "")
        self.composer = self.convert(fullpath, get("COMPOSER") or "")
        self.album_artist = self.convert(fullpath, get("ALBUMARTIST") or "")
        self.author = self.convert(fullpath, get("AUTHOR") or "")
        # todo fix numbers
        self.number = get("TRACKNUMBER")
        self.disc = get("DISCNUMBER")
        self.genre = get("GENRE") or ""
        self.year = get("DATE") or ""
        self.url = get("URL")

        self.comment_source = "COMMENT"
        self.comment = ""
        for field in ["COMMENT", "COMMENT:ID3V1", "SUBTITLE"]:
            val = get(field)
            if val:
                val = self.convert(fullpath, val)
                self.comment_source = field
                self.comment = val
                break

        self.audio = {
            "channels": file_info.channels,
            "bitrate": file_info.bitrate,
            "duration": file_info.length,
            "sample_rate": file_info.sampleRate,
        }

    def __str__(self):
        return self.title + " - " + self.album + " - " + self.artist

    def save(self, file_info, vals_dict):
        def set_prop(prop, name):
            if prop not in vals_dict:
                return
            prev_val = getattr(self, prop)
            val = vals_dict[prop]
            if prev_val != val:
                if val:
                    file_info.tags[name] = [val]
                elif name in file_info.tags:
                    del file_info.tags[name]
                setattr(self, prop, val)

        set_prop("title", "TITLE")
        set_prop("album", "ALBUM")
        set_prop("artist", "ARTIST")
        set_prop("composer", "COMPOSER")
        set_prop("album_artist", "ALBUMARTIST")
        set_prop("author", "AUTHOR")
        set_prop("number", "TRACKNUMBER")
        set_prop("disc", "DISCNUMBER")
        set_prop("genre", "GENRE")
        set_prop("year", "DATE")
        set_prop("url", "URL")

        if "comment" in vals_dict and self.comment != vals_dict["comment"]:
            if vals_dict["comment"]:
                file_info.tags[self.comment_source] = [vals_dict["comment"]]
            else:
                del file_info.tags[self.comment_source]
            self.comment = vals_dict["comment"]
