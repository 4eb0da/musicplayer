import os


def filter_music(file):
    return file.endswith(".mp3") or file.endswith(".m4a")


def glob_music(files):
    for filename in files:
        if os.path.isdir(filename):
            for root, dirnames, filenames in os.walk(filename):
                filenames.sort()
                for file in filenames:
                    if filter_music(file):
                        yield os.path.join(os.getcwd(), root, file)
        elif filter_music(filename):
            yield filename
