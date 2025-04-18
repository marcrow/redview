#!/usr/bin/python3
# Test
from os import mkdir
from os import path
from os import listdir
import shutil
import traceback
import re
from os.path import isfile, join
from src.utils import *
from src.md_redview import MarkdownGetter, MarkdownWritter
from src.ascii_redview import AsciidocGetter, AsciidocWritter

class Directory_Processor:
    def __init__(self, FORMAT : str, src : str, dest : str, ROOT_DEST : str, script_dir : str, dir_to_exclude : list, mainTags : list, real_path : str, exclude_hidden_dir : bool):
        self.script_dir = script_dir
        self.dir_to_exclude = dir_to_exclude
        self.FORMAT = FORMAT
        self.src = src 
        self.dest = dest
        self.ROOT_DEST = ROOT_DEST
        self.exclude_hidden_dir = exclude_hidden_dir
        self.child_dir = []
        try:
            self.child_dir = self.get_directories()
        except Exception:
            traceback.print_exc()
            pass 
        
        self.mainTags = mainTags
        self.real_path = real_path

    
    def get_directories(self):
        directories = [f for f in listdir(self.src) if not isfile(join(self.src, f)) and not f in self.dir_to_exclude]
        if self.exclude_hidden_dir : 
            return [item  for item in directories if not (item.startswith("."))]
        else:
            return [item  for item in directories]

    # Create subdirectories section based on child_dir from self().
    # Return text with links to all subdirectories
    def create_sub_dir_section(self):
        text = ""
        for directory in self.child_dir:
            directory = directory.replace(self.ROOT_DEST,"")
            directory = directory.replace(" ","_")
            if not path.exists(self.dest+directory):
                try:
                    mkdir(self.dest+directory)
                except FileExistsError:
                    print("Directory already exist "+self.dest+directory)
                except Exception as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    return
            # title = "["+Directory+"]("+path+directory+"/)"
            if self.FORMAT == "markmap":
                text = text + "- " + self.format_link(directory,"./"+directory+"/index.html")+"  \n"
            elif self.FORMAT == "md":
                text = text + "- 📁 " + self.format_link(directory,"./"+directory+"/")+"  \n"
            elif self.FORMAT == "obsidian":
                text = text + "- " + self.format_link(directory,"./"+directory+"/"+directory+".md") + "  \n"
            
        return text
    
    def get_category_keyword(self):
        categories = {}
        if self.mainTags is not None:
            if len(self.mainTags) != 1 :
                print("Error : In conf.yaml, only one main tag is authorized")
                exit()
            if isinstance(self.mainTags, list):
                if isinstance(self.mainTags[0], dict):
                    tag = list(self.mainTags[0].keys())[0]
                    return tag.lower()
                else:
                    print( "Error : custom tag in main shall be in a dir structure in conf.yaml")
                    exit()
            else:
                print( "Error : main tag shall be in a list in conf.yaml")
                exit()
        else:
            print("La structure 'main' n'a pas été trouvée dans le fichier YAML.")


    def get_category(self,number):
        categories = {}
        categories = self.mainTags[0][self.get_category_keyword()]
        return categories[number]
    
    def get_files(self):
        return [f for f in listdir(self.src) if isfile(join(self.src, f))]


    def format_link(self, text, destination, header = ""):
        destination = destination.replace(self.ROOT_DEST,"")
        destination = destination.replace(" ","-")
        if len(header) == 0:
            return "["+text.replace("_"," ").replace("\n","")+"]("+destination.replace("\n","")+")  "
        else:
            if self.FORMAT == "md":
                return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+replace_fr_char("".join(header.lower().rstrip().lstrip()).replace(" ","-").replace("(","").replace(")",""))+")  "
            elif self.FORMAT == "obsidian":
                return "[["+destination.replace("\n","")+"#"+header.replace("\n","")+"]]"
            if self.FORMAT == "markmap":
                destination = destination.replace(".md", ".html")
                destination = destination.replace(".adoc", ".html")
                return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip()).replace(" ","-")+")  "
            else:
                return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip())+")  "

    def format_filename_to_title(self, text):
        # handle path with /
        if "/" in text:
            text = text.split("/")[-1]
        if "." in text :
            text = text.split(".")[0]
        text = text.replace("_"," ")
        text = text.replace("\n"," ")
        return text
    
    
    def content_struct_to_text(self, text, content, dpath, level=0):
        # print(content)
        icon_title = "📕 "
        icon_chapter = "🔖 "
        icon_phase = "📑 "
        if self.FORMAT == "markmap":
            icon_title = ""
            icon_chapter = ""
            icon_phase = ""
        if isinstance(content,dict):
            for k,v in content.items():
                #Phase
                if level == 0:
                    h = "##"
                    if len(v) > 0:
                        text= text +h+" "+icon_phase+" "+ self.get_category(k) +"  \n"
                    #Files
                    for elt in v:
                        #For obsidian usage, test relative path
                        #text = content_struct_to_text(text, content[k][elt],  dpath+"/"+elt, level)
                        text = self.content_struct_to_text(text, content[k][elt],  "./"+elt, level +1)
                else:
                    #h1 and h2
                    tlevel = level-2
                    h= ""
                    if level == 1:
                        h = "### "+icon_title
                        
                        print(f'dpath : {dpath}')
                        if dpath.endswith(".md") and "summary.md" not in dpath.lower():
                            title = self.format_filename_to_title(dpath) + " - " + k
                            text = text + h + self.format_link(title, dpath, k) + "  \n"
                        else:
                            text= text +h+ self.format_link(k,dpath,k) +"  \n"
                    else:
                        h = "\t"*tlevel
                        h = h +"- "+icon_chapter
                        text= text +h+ self.format_link(k,dpath,k) +"  \n"

                    for elt in v:
                        text = self.content_struct_to_text(text, elt,  dpath, level+1)
        else: 
            #h3 
            tlevel = level-2
            h = "\t"*tlevel
            h = h +"-"
            if isinstance(content, str):
                text= text +h+" "+icon_chapter+ self.format_link(content,dpath,content) +"  \n"
            else:
                for elt in content:
                    if isinstance(elt, dict):
                        text = self.content_struct_to_text(text, elt,  dpath, level+1)
                    else:
                        text= text +h+" "+icon_chapter+ self.format_link(elt,dpath,elt) +"  \n"
        return text

    def get_content_struct(self):
        content_struct = dict(self.mainTags[0][self.get_category_keyword()])
        for k in content_struct.keys():
            content_struct[k]={}
        return content_struct

    def add_associated_files(self, files):
        text = "# Associated files\n"
        if self.FORMAT == "markmap":
            text = "## Associated files\n"
        for f in files:
            f = f.replace(" ","-") 
            if f == "index.html" or f.lower() == "summary.md": 
                continue
            line = "- ["+f+"]"+"(./"+f+"), \n"
            if self.FORMAT=="markmap" and f[-3:] == ".md": # Use to stay on markmap preview if a md file is open
                if (path.exists(self.dest+f.replace(".md",".html"))):
                    # print(self.dest+f.replace(".md",".html"))
                    line = "- ["+f+"]"+"(./"+f.replace(".md",".html")+"), \n"
                if (path.exists(self.dest+f.replace(".adoc",".html"))):
                    # print(self.dest+f.replace(".md",".html"))
                    line = "- ["+f+"]"+"(./"+f.replace(".adoc",".html")+"), \n"
            text = text + line
        return text
    
    # used by generate_dir_summary to generate the content of summarysc
    def generate_dir_summary_content(self, content, files):
        text_sub_dir = self.create_sub_dir_section()
        text = "" 
        if self.FORMAT == "markmap":
            with open(self.real_path+"/export/web/ressources/template.html", "r") as tf: 
                for line in tf:          
                    text = text + line
        fileName = self.dest.split("/")
        text =text + "# "+self.dest.split("/")[-2].capitalize()+"\n"           
        #Lien vers les réperoires enfants
        if len(text_sub_dir) != 0:
            text = text + "\n## Subcategories \n"
            text = text + text_sub_dir
        if self.FORMAT != "markmap":
            text = text + "# Categories3 :  \n"
        text = self.content_struct_to_text(text,content,self.dest)
        if self.FORMAT != "markmap":
            text = text + self.add_associated_files(files)
        summaryFilename = ""
        if self.FORMAT == "md" or self.FORMAT == "web":
            summaryFilename = "summary.md"
        elif self.FORMAT == "markmap":
            summaryFilename = "index.html"
        else:
            if self.dest[-1]=="/":
                summaryFilename = self.dest.split("/")[-2] + ".md"
            else:
                summaryFilename = self.dest.split("/")[-1] + ".md"
        with open(self.dest+summaryFilename,'w') as wfile:
            wfile.write(text)


    def generate_dir_summary(self):
        files = self.get_files()
        content=self.get_content_struct() 
        file_list = []
        #Copy every files + load titles + add md toc
        for cfile in files :
            if cfile[-3:] == ".md":
                markdown_getter = MarkdownGetter(self.FORMAT, self.src , self.dir_to_exclude , self.mainTags, self.real_path) 
                markdown_writter = MarkdownWritter(self.FORMAT, self.dest, self.ROOT_DEST,  self.mainTags, self.real_path)
                markdown_writter.process_markdown_file(cfile, content, markdown_getter)
            elif cfile[-5:] == ".adoc" and cfile.lower() != "summary.adoc":
                asciidocGetter = AsciidocGetter(self.FORMAT, self.src , self.dir_to_exclude , self.mainTags, self.real_path)
                asciidocWritter = AsciidocWritter(self.FORMAT, self.dest, self.ROOT_DEST,  self.mainTags, self.real_path)
                asciidocWritter.process_asciidoc_file(cfile, content, asciidocGetter)
            else:
                dest = self.dest+cfile.replace(" ","-")
                if not path.isfile(dest):
                    is_ignored = False
                    for ignnore_type in [".swp",".swx", "swpx"]:
                        if dest.endswith(ignnore_type):
                            is_ignored=True
                    if not is_ignored:        
                        shutil.copy(self.src+cfile, dest)
            file_list.append(cfile)
        if self.FORMAT == "web":
            self.FORMAT="markmap"
            self.generate_dir_summary_content(content, files)
            self.FORMAT="md"
            self.generate_dir_summary_content(content, files)
            self.FORMAT = "web"
        else:
            self.generate_dir_summary_content(content, files)
            
        
        