import os


def glob_music(dir):
    for root, dirnames, filenames in os.walk(dir):
        filenames.sort()
        for file in filenames:
            if file.endswith(".mp3") or file.endswith(".m4a"):
                yield os.path.join(os.getcwd(), root, file)
