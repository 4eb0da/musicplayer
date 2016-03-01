import re


class TrackInfo:
    @staticmethod
    def check_tags(tags):
        return (
            tags and
            tags["TITLE"] and tags["TITLE"][0] and
            tags["ALBUM"] and tags["ALBUM"][0] and
            tags["ARTIST"] and tags["ARTIST"][0]
        )

    # russian letters encoding fix
    LETTERS = "абвгдеёжзийклмнопрстуфхцчшщьыъэюя"
    LETTERS += LETTERS.upper()
    LETTERS = LETTERS.encode("cp1251").decode("cp1252")

    @staticmethod
    def convert(string):
        if re.search("[" + TrackInfo.LETTERS + "]", string):
            return string.encode("cp1252").decode("cp1251")
        return string

    def __init__(self, tags):
        self.title = self.convert(tags["TITLE"][0])
        self.album = self.convert(tags["ALBUM"][0])
        self.artist = self.convert(tags["ARTIST"][0])

    def __str__(self):
        return self.title + " - " + self.album + " - " + self.artist
