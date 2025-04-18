#!/usr/bin/python3
# Test
from os import mkdir
from os import rmdir
from os import path
from os import listdir
from os import walk
from os import makedirs
from os import symlink
from os import remove
from os import readlink
import time
from shutil import rmtree
import shutil
import re
from os.path import isfile, join
import argparse
import textwrap
from src.utils import *
from src.dir_processor import Directory_Processor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timedelta

class Watcher:

    def __init__(self, redviewGenerator):
        self.redviewGenerator = redviewGenerator
        self.DIRECTORY_TO_WATCH = self.redviewGenerator.src
        self.observer = Observer()
        

    def run(self):
        event_handler = Handler(self.redviewGenerator)
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
    def __init__(self, redviewGenerator):
        self.redviewGenerator = redviewGenerator
        self.DIRECTORY_TO_WATCH = self.redviewGenerator.src
        self.ignore_types = [".swp",".swx", "swpx"]
        # Track recently processed directories to avoid redundant processing
        self.last_summary_times = {}
        self.summary_interval = timedelta(seconds=1)

    def process(self, event):
        print("Event occurred: ", event.event_type, event.src_path, path.dirname(event.src_path))
        if self.ignore_file(event.src_path):
            return 0
            
        # Validate that the path is within our watched directory
        if not self.is_path_valid(event.src_path):
            print(f"Warning: Path {event.src_path} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
            
        dest_file = event.src_path.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
        dest_directory = path.dirname(dest_file)
        dest_directory = clean_end_path(dest_directory)
        targetsummary = clean_end_path(path.dirname(event.src_path))

        if event.event_type == "deleted":
            dest_file = dest_directory
            if not path.exists(targetsummary):
                print("parent directory also deleted")
                return
        
        # Ensure the target directory is within the watched directory
        if not targetsummary.startswith(self.DIRECTORY_TO_WATCH):
            print(f"Warning: Target summary path {targetsummary} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
                 
        # Generate directory summary
        print("generate summary "+targetsummary+ " to "+dest_directory)
        dir_processor = Directory_Processor(
            self.redviewGenerator.FORMAT, 
            targetsummary, 
            dest_directory, 
            self.redviewGenerator.ROOT_DEST, 
            self.redviewGenerator.script_dir, 
            self.redviewGenerator.dir_to_exclude, 
            self.redviewGenerator.mainTags, 
            self.redviewGenerator.real_path, 
            self.redviewGenerator.exclude_hidden_dir
        )
        dir_processor.generate_dir_summary()
        self.summary_event(event)

        print("Event processed: ", event.event_type, event.src_path, path.dirname(event.src_path)+"\n")

    def is_path_valid(self, src_path):
        """Check if the path is within our watched directory"""
        # Handle None paths (shouldn't happen but just in case)
        if src_path is None:
            return False
            
        try:
            # Normalize paths to absolute paths
            abs_src_path = path.abspath(src_path)
            abs_watch_dir = path.abspath(self.DIRECTORY_TO_WATCH)
            
            # Check if the path starts with our watched directory
            return abs_src_path.startswith(abs_watch_dir)
        except Exception as err:
            print(f"Error validating path: {err=}, {type(err)=}")
            return False

    def on_modified(self, event):
        self.process(event)

    def on_moved(self, event):
        """Handle file/directory move events by updating both source and destination directories"""
        if self.ignore_file(event.src_path) or self.ignore_file(event.dest_path):
            return 0
            
        # Validate that both paths are within our watched directory
        if not self.is_path_valid(event.src_path) or not self.is_path_valid(event.dest_path):
            print(f"Warning: Path {event.src_path} or {event.dest_path} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
            
        # Handle the source directory (where the file was moved from)
        src_directory = clean_end_path(path.dirname(event.src_path))
        dest_src_directory = src_directory.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
        dest_src_directory = clean_end_path(dest_src_directory)
        
        # Handle the destination directory (where the file was moved to)
        dest_directory = clean_end_path(path.dirname(event.dest_path))
        dest_dest_directory = dest_directory.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
        dest_dest_directory = clean_end_path(dest_dest_directory)
        
        # Ensure both directories are within the watched directory
        if not src_directory.startswith(self.DIRECTORY_TO_WATCH) or not dest_directory.startswith(self.DIRECTORY_TO_WATCH):
            print(f"Warning: Source or destination directory is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
            
        # Handle case where file is moved to a parent directory
        if not path.exists(src_directory) and path.exists(dest_directory):
            print(f"File moved to parent directory: {event.src_path} -> {event.dest_path}")
            # Only process the destination directory in this case
            src_directory = dest_directory
            dest_src_directory = dest_dest_directory
        
        # Create symlink for the moved file in the destination directory
        if not event.is_directory:
            dest_file = event.dest_path.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
            try:
                if path.exists(dest_file):
                    if path.islink(dest_file):
                        remove(dest_file)
                    elif path.isdir(dest_file):
                        rmtree(dest_file)
                
                target = event.dest_path
                if path.islink(event.dest_path):
                    target = readlink(event.dest_path)
                    target = target.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
                
                print(f"Creating symlink from {target} to {dest_file}")
                symlink(target, dest_file)
            except Exception as err:
                print(f"Error creating symlink: {err=}, {type(err)=}")
        
        # Update source directory summary
        print(f"Updating source directory summary: {src_directory} to {dest_src_directory}")
        src_processor = Directory_Processor(
            self.redviewGenerator.FORMAT,
            src_directory,
            dest_src_directory,
            self.redviewGenerator.ROOT_DEST,
            self.redviewGenerator.script_dir,
            self.redviewGenerator.dir_to_exclude,
            self.redviewGenerator.mainTags,
            self.redviewGenerator.real_path,
            self.redviewGenerator.exclude_hidden_dir
        )
        src_processor.generate_dir_summary()
        
        # Update destination directory summary
        print(f"Updating destination directory summary: {dest_directory} to {dest_dest_directory}")
        dest_processor = Directory_Processor(
            self.redviewGenerator.FORMAT,
            dest_directory,
            dest_dest_directory,
            self.redviewGenerator.ROOT_DEST,
            self.redviewGenerator.script_dir,
            self.redviewGenerator.dir_to_exclude,
            self.redviewGenerator.mainTags,
            self.redviewGenerator.real_path,
            self.redviewGenerator.exclude_hidden_dir
        )
        dest_processor.generate_dir_summary()
        
        # Update timestamps for both directories
        self.last_summary_times[src_directory] = datetime.now()
        self.last_summary_times[dest_directory] = datetime.now()

    def on_created(self, event):
        if self.ignore_file(event.src_path):
            return 0
            
        # Validate that the path is within our watched directory
        if not self.is_path_valid(event.src_path):
            print(f"Warning: Path {event.src_path} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
        
        # Get the parent directory of the created file/directory
        parent_dir = clean_end_path(path.dirname(event.src_path))
        
        # Ensure the parent directory is within the watched directory
        if not parent_dir.startswith(self.DIRECTORY_TO_WATCH):
            print(f"Warning: Parent directory {parent_dir} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
            
        # Make sure parent_dir exists (could be created by another process)
        if not path.exists(parent_dir):
            print(f"Warning: Parent directory {parent_dir} does not exist")
            try:
                makedirs(parent_dir, exist_ok=True)
                print(f"Created parent directory: {parent_dir}")
            except Exception as err:
                print(f"Error creating parent directory: {err=}, {type(err)=}")
                return 0
            
        dest_file = event.src_path.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
        if event.is_directory:
            print("create dir "+dest_file)
            try:
                makedirs(dest_file, exist_ok=True)
            except FileExistsError:
                return
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                return
        else:
            try:
                # Handle case where directory is generated in place of symlink to a directory
                if path.exists(dest_file) and path.isdir(dest_file) and path.islink(event.src_path):
                    rmtree(dest_file)
                if not path.exists(dest_file):
                    target = event.src_path
                    location = dest_file
                    if path.islink(event.src_path):
                        target = readlink(event.src_path)
                        target = target.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
                    print("create symlink from "+target + " to " + location)
                    symlink(target, location)
            except FileExistsError:
                print(dest_file +" FileExistsError -> skipped")
                return
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                return 
                
        # Only process if we haven't recently processed this directory
        if datetime.now() - self.last_summary_times.get(parent_dir, datetime.min) >= self.summary_interval or event.is_directory:
            self.last_summary_times[parent_dir] = datetime.now()
            self.process(event)

    def on_deleted(self, event):
        if self.ignore_file(event.src_path):
            return 0
            
        # Validate that the path is within our watched directory
        if not self.is_path_valid(event.src_path):
            print(f"Warning: Path {event.src_path} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
        
        # Get the parent directory of the deleted file/directory
        parent_dir = clean_end_path(path.dirname(event.src_path))
        
        # Ensure the parent directory is within the watched directory
        if not parent_dir.startswith(self.DIRECTORY_TO_WATCH):
            print(f"Warning: Parent directory {parent_dir} is outside the watched directory {self.DIRECTORY_TO_WATCH}")
            return 0
            
        dest_file = event.src_path.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
        # when directory is deleted
        if event.is_directory:
            print("delete dir "+dest_file)
            try:
                rmtree(dest_file)
            except FileNotFoundError:
                return
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                return
        # when file is deleted
        else:
            print("delete file "+dest_file)
            try:
                remove(dest_file)
            except FileNotFoundError:
                # if a directory is deleted, the delete file event for a file from the deleted directory can be generated before the directory event itself
                return
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                return
                
        self.process(event)
        if parent_dir in self.last_summary_times:
            del self.last_summary_times[parent_dir]
    
    def ignore_file(self, src_path):
        # Handle None paths
        if src_path is None:
            return True
            
        try:
            for ignore_type in self.ignore_types:
                if src_path.endswith(ignore_type):
                    return True 
            return False
        except Exception:
            # If we can't check the path, better to ignore it
            return True
    
    def summary_event(self, event):
        parent_dir = clean_end_path(path.dirname(event.src_path))
        self.last_summary_times[parent_dir] = datetime.now()



class RedviewGenerator:
    def __init__(self, FORMAT : str, src : str, dest : str, script_dir : str, dir_to_exclude : list, exclude_hidden_dir : bool, mainTags : list):
        self.FORMAT = FORMAT
        self.src = src 
        self.dest = dest
        self.ROOT_DEST = dest
        self.script_dir = script_dir
        self.dir_to_exclude = dir_to_exclude
        self.exclude_hidden_dir = exclude_hidden_dir
        self.mainTags = mainTags
        self.real_path = path.dirname(path.realpath(__file__))
        


    def export_web(self):
        source_directory = self.script_dir + "/export/web/"
        destination_directory = self.ROOT_DEST

        # Copie les fichiers du répertoire source vers le répertoire de destination
        #for root, dirs, files in walk(source_directory):
        # Copie les répertoires du répertoire source vers le répertoire de destination
        for root, dirs, files in walk(source_directory):
            for file in files:
                source_file = path.join(root, file)
                destination_file = path.join(destination_directory, path.relpath(source_file, source_directory))
                makedirs(path.dirname(destination_file), exist_ok=True)
                shutil.copy2(source_file, destination_file)
            for dir in dirs:
                source_dir = path.join(root, dir)
                destination_dir = path.join(destination_directory, path.relpath(source_dir, source_directory))
                makedirs(destination_dir, exist_ok=True)


    
    
    @staticmethod
    def last_slash_index(path):
        if path[-1] == "/":
            path = path[:-1]
        if path.rfind("/") != -1:
            return path[:path.rfind("/")]
        return path

    def goto_parent_dir(self):
        self.src =  RedviewGenerator.last_slash_index(self.src)
        self.dest = RedviewGenerator.last_slash_index(self.dest)
           # self.markdown_getter.src = self.markdown_getter.src[:self.markdown_getter.src.rfind("/")]


    def generate_doc(self):
        dir_processor = Directory_Processor(self.FORMAT, self.src, self.dest, self.ROOT_DEST, self.script_dir ,self.dir_to_exclude, self.mainTags, self.real_path, self.exclude_hidden_dir)
        dir_processor.generate_dir_summary()
        
        # Create symlinks for files in the current (root) directory
        for file_name in listdir(self.src):
            full_file_name = path.join(self.src, file_name)
            if path.isfile(full_file_name):
                link_name = path.join(self.dest, file_name)
                if not path.exists(link_name):
                    symlink(full_file_name, link_name)
        
        for directory in dir_processor.child_dir:           
            self.src = clean_end_path(self.src+"/"+directory)
            self.dest = clean_end_path(self.dest+"/"+directory.replace(" ","_"))
            # dir_markdown_getter = MarkdownGetter(markdown_getter.FORMAT, markdown_getter.src+"/"+directory, markdown_getter.dest+"/"+directory, markdown_getter.dir_to_exclude, markdown_getter.mainTags) 
            # dir_markdown_writter = MarkdownWritter(markdown_writter.FORMAT, markdown_writter.dest+"/"+directory,  markdown_writter.mainTags)
            #generate_doc(dir_markdown_getter, markdown_writter)
            self.generate_doc()
             # Copy all files in the current source directory to the destination directory
            for file_name in listdir(self.src):
                full_file_name = path.join(self.src, file_name)
                if path.isfile(full_file_name):
                    link_name = path.join(self.dest, file_name)
                    if not path.exists(link_name):
                        symlink(full_file_name, link_name)
            self.goto_parent_dir()

    """Used to copy all files in a dest directory, to limit web server configuration disclosure"""
    def dest_to_data(self):
        self.dest = self.dest + "/data/"
        self.ROOT_DEST = self.ROOT_DEST + "/data/"
        makedirs(path.dirname(self.dest), exist_ok=True)


#------------------Create document---------------
        

def redview_title():
    text ="""
 _  .-')     ('-.  _ .-') _        (`-.              ('-.    (`\ .-') /`
( \( -O )  _(  OO)( (  OO) )     _(OO  )_          _(  OO)    `.( OO ),'
 ,------. (,------.\     .'_ ,--(_/   ,. \ ,-.-') (,------.,--./  .--.  
 |   /`. ' |  .---',`'--..._)\   \   /(__/ |  |OO) |  .---'|      |  |  
 |  /  | | |  |    |  |  \  ' \   \ /   /  |  |  \ |  |    |  |   |  |, 
 |  |_.' |(|  '--. |  |   ' |  \   '   /,  |  |(_/(|  '--. |  |.'.|  |_)
 |  .  '.' |  .--' |  |   / :   \     /__),|  |_.' |  .--' |         |  
 |  |\  \  |  `---.|  '--'  /    \   /   (_|  |    |  `---.|   ,'.   |  
 `--' '--' `------'`-------'      `-'      `--'    `------''--'   '--'  

"""
    return text


# Define argparse
def main():
    parser = argparse.ArgumentParser(add_help=False,prog='redview.py',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent(redview_title()))
    parser.add_argument("--source", "-s", help="Source directory wich contains original md files", required=True)             
    parser.add_argument("--name", "-n", help="Nom du projet, par défaut redview",  default="redview", required=False)
    parser.add_argument("--path", "-p", help="Chemin destination de des notes formatées, par défaut /tmp/",  default="/tmp/", required=False)
    parser.add_argument("--format", "-f", help="Format de sortie optimisée pour : web, obsidian et markmap", choices=["web","md","obsidian","markmap"], default="web")
    parser.add_argument("--watcher", "-w", help="Run redview in the background and update automatically note from source to path", action="store_true")
    parser.add_argument("--verbose", "-v", help="Augmente le niveau de verbosité",action="store_true")
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, 
                    help='Show this help message and exit.')
    
    
    args = parser.parse_args()

    FORMAT = args.format

    dest_path = args.path
    dest_dir = args.name
    dest = dest_path + dest_dir 
    dest = clean_end_path(dest)

    script_dir = path.dirname(path.realpath(__file__))
    dir_to_exclude = getDirToExclude(script_dir+"/conf.yaml")
    exclude_hidden_dir = hiddenDirSettings(script_dir+"/conf.yaml")
    mainTags = getMainTags(script_dir+"/conf.yaml")



    # src = path.dirname(path.realpath(__file__))

    src = args.source
    src = clean_end_path(src)
    if not path.exists(src):
        print("error: Source directory "+src+" not found")
        exit()

    if not path.exists(dest_path):
        print("error: "+dest_path+" not found")
        exit()


    if path.exists(dest):
        rmtree(dest)
        # print("Old "+dest+" directorty found")
        # ans = input("Do you want to replace it? (y/n)")
        # if ans != "y":
        #     print("ok") #Shall be replaced by the launch of grip
        #     exit()
        # else:
        #     rmtree(dest)

    mkdir(dest)
    redview = RedviewGenerator(FORMAT, src, dest, script_dir, dir_to_exclude, exclude_hidden_dir, mainTags)

    # markdown_getter = MarkdownGetter(FORMAT, src, dest , dir_to_exclude , mainTags) 
    # markdown_writter = MarkdownWritter(FORMAT, dest, mainTags)
    if FORMAT == "web" :
            redview.export_web()
            redview.dest_to_data()

    redview.generate_doc()
    
    if args.watcher:
        w = Watcher(redview)
        w.run()

if __name__ == '__main__':
    main()
