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
        self.ignore_types = [".swp",".swx", "swpx"]
        self.ignore_next = ""
        #Use to avoid to generate multiple time the directory summary
        # Also, because sometimes there is no modification event after a file creation.
        self.last_summary_times = {}
        self.summary_interval = timedelta(seconds=1)

    def process(self, event):
        """
        Événement détecté.
        """
        print("Event occurr: ", event.event_type, event.src_path, path.dirname(event.src_path))
        if self.ignore_file(event.src_path):
            # print(event.src_path+" ignored")
            return 0
        if self.ignore_next == event.src_path:
            # print(event.src_path+" ignored")
            self.ignore_next=""
            return 0
        dest_file = event.src_path.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
        dest_directory = path.dirname(dest_file)
        # print("dest_directory "+ dest_directory)
        # print("dest_file "+ dest_file)
        #targetsummary = clean_end_path(event.src_path)
        targetDir = clean_end_path(dest_directory)
        # if not event.is_directory:
        targetsummary = clean_end_path(path.dirname(event.src_path))
        #targetDir = clean_end_pathpath(dest_directory)
        if event.event_type == "created" :
            # when directory is created
            if event.is_directory:
                print("create dir "+dest_file)
                try:
                    makedirs(dest_file, exist_ok=True)
                except FileExistsError:
                    return
                except Exception as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    return
#----- Add code here to generate empty summary in the new directory TBD ------
                # targetsummary = clean_end_path(path.dirname(event.src_path))
            # when file is created
            else:
                print("create symlink "+dest_file)
                try:
                    if path.exists(dest_file):
                        rmtree(dest_file)
                    target = event.src_path
                    location = dest_file
                    if path.islink(event.src_path):
                        print("it is a link "+event.src_path)
                        target = readlink(event.src_path)
                        target = target.replace(self.redviewGenerator.src, self.redviewGenerator.ROOT_DEST)
                    symlink(target,location)
                except FileExistsError:
                    print(dest_file +"FileExistsError -> skipped")
                    return
                except Exception as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    return 
        if event.event_type == "deleted" :
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
            
            if not path.exists(targetsummary):
                print("parent directory also deleted")
                return
            dest_file = dest_directory
        
        # when directories are created or suppressed
        if event.event_type != "modified" and event.is_directory :
            #targetDir = clean_end_path(dest_file)
            print("generate summary "+targetsummary+ " to "+targetDir)
            dir_processor = Directory_Processor(self.redviewGenerator.FORMAT, targetsummary, targetDir, self.redviewGenerator.ROOT_DEST, self.redviewGenerator.script_dir, self.redviewGenerator.dir_to_exclude, self.redviewGenerator.mainTags, self.redviewGenerator.real_path, self.redviewGenerator.exclude_hidden_dir)
            dir_processor.generate_dir_summary()
            self.summary_event(event)
        # when files are modified, created and suppressed. 
        # If creation is excluded from the condition definition, this is because every file creation event is followed by a file modification event.
        # And we don't want to duplicate generate_me calls for nothing
        elif not event.is_directory :
            if event.event_type == "created":
                last_modification = datetime.now() - self.last_summary_times.get(path, datetime.min)
                if last_modification < self.summary_interval:
                    print("the summary has already been generated "+ str(last_modification)+ " - "+targetsummary)
                    return
                else:
                    print("we will generate a summary - "+targetsummary)
            print("generate summary "+targetsummary+ " to "+targetDir)
            dir_processor = Directory_Processor(self.redviewGenerator.FORMAT, targetsummary, targetDir, self.redviewGenerator.ROOT_DEST, self.redviewGenerator.script_dir, self.redviewGenerator.dir_to_exclude, self.redviewGenerator.mainTags, self.redviewGenerator.real_path, self.redviewGenerator.exclude_hidden_dir)
            dir_processor.generate_dir_summary()
            self.summary_event(event)

        print("Event occurred: ", event.event_type, event.src_path, path.dirname(event.src_path))

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)
        path = event.src_path
        if datetime.now() - self.last_summary_times.get(path, datetime.min) >= self.summary_interval:
            
            self.last_summary_times[path] = datetime.now()

    def on_deleted(self, event):
        self.process(event)
        if path in self.last_summary_times:
            del self.last_summary_times[path]
    
    def ignore_file(self,src_path):
        for ignore_type in self.ignore_types:
            if src_path.endswith(ignore_type):
                directory_path = path.dirname(src_path)
                self.ignore_next = directory_path
                return True 
        return False
    
    def summary_event(self,event):
        path = event.src_path
        self.last_summary_times[path] = datetime.now()

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
        for root, dirs, files in walk(source_directory):
            for file in files:
                source_file = path.join(root, file)
                destination_file = path.join(destination_directory, path.relpath(source_file, source_directory))
                makedirs(path.dirname(destination_file), exist_ok=True)
                shutil.copy2(source_file, destination_file)

        # Copie les répertoires du répertoire source vers le répertoire de destination
        for root, dirs, files in walk(source_directory):
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
        for directory in dir_processor.child_dir:
            self.src = clean_end_path(self.src+"/"+directory)
            self.dest = clean_end_path(self.dest+"/"+directory.replace(" ","_"))
            # dir_markdown_getter = MarkdownGetter(markdown_getter.FORMAT, markdown_getter.src+"/"+directory, markdown_getter.dest+"/"+directory, markdown_getter.dir_to_exclude, markdown_getter.mainTags) 
            # dir_markdown_writter = MarkdownWritter(markdown_writter.FORMAT, markdown_writter.dest+"/"+directory,  markdown_writter.mainTags)
            #generate_doc(dir_markdown_getter, markdown_writter)
            self.generate_doc()
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