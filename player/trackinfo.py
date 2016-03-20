import re
import os


class TrackInfo:
    # russian letters encoding fix
    LETTERS = "абвгдеёжзийклмнопрстуфхцчшщьыъэюя"
    LETTERS += LETTERS.upper()
    LETTERS = LETTERS.encode("cp1251").decode("cp1252")

    @staticmethod
    def convert(string):
        if re.search("[" + TrackInfo.LETTERS + "]", string):
            try:
                return string.encode("cp1252").decode("cp1251")
            except:
                return string
        return string

    def __init__(self, fullpath, tags, file_info):
        def get(name):
            return name in tags and len(tags[name]) and tags[name][0] or ""

        self.title = self.convert(get("TITLE")) or os.path.basename(fullpath)
        self.album = self.convert(get("ALBUM") or "Unknown")
        self.artist = self.convert(get("ARTIST") or "Unknown")
        self.composer = self.convert(get("COMPOSER") or "Unknown")
        self.album_artist = self.convert(get("ALBUMARTIST") or "Unknown")
        self.author = self.convert(get("AUTHOR") or "Unknown")
        # todo fix numbers
        self.number = get("TRACKNUMBER")
        self.disc = get("DISCNUMBER")
        self.genre = get("GENRE") or "Unknown"
        self.year = get("DATE") or "Unknown"
        self.url = get("URL")
        self.comment = self.convert(get("COMMENT") or get("COMMENT:ID3V1"))

        self.audio = {
            "channels": file_info.channels,
            "bitrate": file_info.bitrate,
            "duration": file_info.length,
            "sample_rate": file_info.sampleRate,
        }

    def __str__(self):
        return self.title + " - " + self.album + " - " + self.artist
