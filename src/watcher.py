import sys
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:

    def __init__(self, watch_directory):
        self.DIRECTORY_TO_WATCH = watch_directory
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    def __init__(self):
        self.ignore_types = [".swp",".swx", "swpx"]
        self.ignore_next = ""

    def process(self, event):
        """
        Événement détecté.
        """
        if self.ignore_file(event.src_path):
            print(event.src_path+" ignored")
            return 0
        if self.ignore_next == event.src_path:
            print(event.src_path+" ignored")
            self.ignore_next=""
            return 0
        print("Event occurred: ", event.event_type, event.src_path)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)
    
    def ignore_file(self,src_path):
        for ignore_type in self.ignore_types:
            if src_path.endswith(ignore_type):
                directory_path = os.path.dirname(src_path)
                self.ignore_next = directory_path
                return True 
        return False
            


if __name__ == '__main__':
    watch_directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    w = Watcher(watch_directory)
    w.run()