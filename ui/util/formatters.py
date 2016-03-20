def duration(time):
    time = int(time)
    mins = time // 60
    secs = time % 60
    if secs < 10:
        secs = "0" + str(secs)
    return str(mins) + ":" + str(secs)
