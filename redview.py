#!/usr/bin/python3
# Test
from os import mkdir
from os import rmdir
from os import path
from os import listdir
from os import walk
from os import makedirs
from shutil import rmtree
import shutil
import re
from os.path import isfile, join
import argparse
import textwrap
from src.utils import *
from src.dir_processor import Directory_Processor

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


    def get_directories(self):
        directories = [f for f in listdir(self.src) if not isfile(join(self.src, f)) and not f in self.dir_to_exclude]
        if self.exclude_hidden_dir : 
            return [item  for item in directories if not (item.startswith("."))]
        else:
            return [item  for item in directories]
    
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
        dir = self.get_directories()
        dir_processor = Directory_Processor(self.FORMAT, self.src, self.dest, self.ROOT_DEST, self.script_dir, dir ,self.dir_to_exclude, self.mainTags, self.real_path)
        dir_processor.generate_readme()
        for directory in dir:
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
    if FORMAT == "web" or "markmap" or "md":
            redview.export_web()
            redview.dest_to_data()

    if FORMAT == "web":
        redview.FORMAT = "markmap"
        redview.generate_doc()
        redview = RedviewGenerator("md", src, dest, script_dir, dir_to_exclude, exclude_hidden_dir, mainTags)
        redview.dest_to_data()
    redview.generate_doc()

if __name__ == '__main__':
    main()