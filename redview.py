#!/usr/bin/python3

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
from src.md_redview import MarkdownGetter
from src.md_redview import MarkdownWritter

class RedviewGenerator:
    def __init__(self, FORMAT : str, src : str, dest : str, script_dir : str, dir_to_exclude : list, mainTags : list):
        self.script_dir = script_dir
        self.dir_to_exclude = dir_to_exclude
        self.markdown_getter = MarkdownGetter(FORMAT, src , dir_to_exclude , mainTags, path.dirname(path.realpath(__file__))) 
        self.markdown_writter = MarkdownWritter(FORMAT, dest, mainTags, self.get_directories(), path.dirname(path.realpath(__file__)))
        if FORMAT == "web" or "markmap" or "md":
            self.export_web()

    def export_web(self):
        source_directory = self.script_dir + "/export/web/"
        destination_directory = self.markdown_writter.ROOT_DEST

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
        directories = [f for f in listdir(self.markdown_getter.src) if not isfile(join(self.markdown_getter.src, f)) and not f in self.dir_to_exclude]
        return [item  for item in directories if not (item.startswith("."))]
    
    @staticmethod
    def last_slash_index(path):
        if path[-1] == "/":
            path = path[:-1]
        if path.rfind("/") != -1:
            return path[:path.rfind("/")]
        return path

    def goto_parent_dir(self):
        self.markdown_getter.src =  RedviewGenerator.last_slash_index(self.markdown_getter.src)
        self.markdown_writter.dest = RedviewGenerator.last_slash_index(self.markdown_writter.dest)
           # self.markdown_getter.src = self.markdown_getter.src[:self.markdown_getter.src.rfind("/")]
        
        

    def generate_doc(self):
        dir = self.get_directories()
        self.markdown_writter.child_dir = dir
        if self.markdown_getter.FORMAT == "markmap":
            self.markdown_writter.generate_markmap_readme(self.markdown_getter)
        else :
            self.markdown_writter.generate_readme(self.markdown_getter)
        for directory in dir:
            self.markdown_getter.src = clean_end_path(self.markdown_getter.src+"/"+directory)
            self.markdown_writter.dest = clean_end_path(self.markdown_writter.dest+"/"+directory.replace(" ","_"))
            # dir_markdown_getter = MarkdownGetter(markdown_getter.FORMAT, markdown_getter.src+"/"+directory, markdown_getter.dest+"/"+directory, markdown_getter.dir_to_exclude, markdown_getter.mainTags) 
            # dir_markdown_writter = MarkdownWritter(markdown_writter.FORMAT, markdown_writter.dest+"/"+directory,  markdown_writter.mainTags)
            #generate_doc(dir_markdown_getter, markdown_writter)
            self.generate_doc()
            self.goto_parent_dir()
        

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
    mainTags = getMainTags(script_dir+"/conf.yaml")



    # src = path.dirname(path.realpath(__file__))

    src = args.source

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
    redview = RedviewGenerator(FORMAT, src, dest, script_dir, dir_to_exclude, mainTags)
    # markdown_getter = MarkdownGetter(FORMAT, src, dest , dir_to_exclude , mainTags) 
    # markdown_writter = MarkdownWritter(FORMAT, dest, mainTags)
    if FORMAT == "web":
        redview.markdown_getter.FORMAT = "markmap"
        redview.markdown_writter.FORMAT = "markmap"
        redview.generate_doc()
        redview.markdown_getter.FORMAT = "md"
        redview.markdown_writter.FORMAT = "md"
    redview.generate_doc()

if __name__ == '__main__':
    main()