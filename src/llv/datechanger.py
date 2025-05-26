import os
import time

pfad = r"C:\Users\mschulz\Pictures\boom.png"
neue_mtime = time.mktime((1990, 1, 1, 12, 34, 0, 0, 0, -1))
# (atime = Zugriffszeit), hier gleichsetzen mit mtime
os.utime(pfad, (neue_mtime, neue_mtime))

print("Änderungsdatum gesetzt auf:", time.ctime(neue_mtime))
