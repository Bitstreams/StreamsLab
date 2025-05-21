from logging.handlers import RotatingFileHandler
import os

class ManagedRotatingFileHandler(RotatingFileHandler):
    def rotation_filename(self, default_name):
        path, log_name = os.path.split(default_name)
        filename, index = os.path.splitext(log_name)
        base, extension = os.path.splitext(filename)
        new_name = f"{base}{index}{extension}"
        return os.path.join(path, new_name)