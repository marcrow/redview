#!/usr/bin/python3
# Test
from os import mkdir, makedirs
from os import path
from os import listdir
import shutil
import traceback
import re
from os.path import isfile, join, exists, isdir
from src.utils import *
from src.md_redview import MarkdownGetter, MarkdownWritter
from src.ascii_redview import AsciidocGetter, AsciidocWritter

class Directory_Processor:
    def __init__(self, FORMAT : str, src : str, dest : str, ROOT_DEST : str, script_dir : str, dir_to_exclude : list, mainTags : list, real_path : str, exclude_hidden_dir : bool):
        self.script_dir = script_dir
        self.dir_to_exclude = dir_to_exclude
        self.FORMAT = FORMAT
        # Ensure src and dest paths are properly formatted (no trailing slash unless root)
        self.src = clean_end_path(src) + '/' if not src.endswith('/') else src
        self.dest = clean_end_path(dest) + '/' if not dest.endswith('/') else dest
        self.ROOT_DEST = ROOT_DEST
        self.exclude_hidden_dir = exclude_hidden_dir
        self.child_dir = []
        
        # Create destination directory if it doesn't exist
        if not exists(self.dest):
            try:
                makedirs(self.dest, exist_ok=True)
                print(f"Created directory: {self.dest}")
            except Exception as e:
                print(f"Error creating directory {self.dest}: {e}")
        
        # Only try to get directories if source path exists
        if exists(self.src) and isdir(self.src):
            try:
                self.child_dir = self.get_directories()
            except Exception as e:
                print(f"Error getting directories from {self.src}: {e}")
                traceback.print_exc()
        else:
            print(f"Warning: Source directory does not exist: {self.src}")
        
        self.mainTags = mainTags
        self.real_path = real_path

    
    def get_directories(self):
        # Check if source directory exists before trying to list it
        if not exists(self.src) or not isdir(self.src):
            print(f"Warning: Cannot list non-existent directory: {self.src}")
            return []
            
        try:
            directories = [f for f in listdir(self.src) if not isfile(join(self.src, f)) and not f in self.dir_to_exclude]
            if self.exclude_hidden_dir : 
                return [item for item in directories if not (item.startswith("."))]
            else:
                return [item for item in directories]
        except FileNotFoundError:
            print(f"Warning: Directory not found: {self.src}")
            return []
        except PermissionError:
            print(f"Warning: Permission denied when accessing: {self.src}")
            return []
        except Exception as e:
            print(f"Error listing directory {self.src}: {e}")
            return []

    # Create subdirectories section based on child_dir from self().
    # Return text with links to all subdirectories
    def create_sub_dir_section(self):
        text = ""
        for directory in self.child_dir:
            directory = directory.replace(self.ROOT_DEST,"")
            directory = directory.replace(" ","_")
            target_dir = self.dest+directory
            
            if not path.exists(target_dir):
                try:
                    makedirs(target_dir, exist_ok=True)
                except FileExistsError:
                    print(f"Directory already exists: {target_dir}")
                except Exception as err:
                    print(f"Unexpected error creating directory {target_dir}: {err=}, {type(err)=}")
                    continue
            
            # Format links based on output format
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
        # Check if source directory exists before trying to list files
        if not exists(self.src) or not isdir(self.src):
            print(f"Warning: Cannot list files in non-existent directory: {self.src}")
            return []
            
        try:
            return [f for f in listdir(self.src) if isfile(join(self.src, f))]
        except FileNotFoundError:
            print(f"Warning: Directory not found when listing files: {self.src}")
            return []
        except PermissionError:
            print(f"Warning: Permission denied when listing files in: {self.src}")
            return []
        except Exception as e:
            print(f"Error listing files in directory {self.src}: {e}")
            return []


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
            template_path = self.real_path+"/export/web/ressources/template.html"
            if exists(template_path):
                try:
                    with open(template_path, "r") as tf: 
                        for line in tf:          
                            text = text + line
                except Exception as e:
                    print(f"Error reading template file {template_path}: {e}")
            else:
                print(f"Warning: Template file not found: {template_path}")
                
        # Get directory name for title
        dir_parts = self.dest.rstrip('/').split("/")
        dir_name = dir_parts[-1] if dir_parts else "Root"
        text = text + "# " + dir_name.capitalize() + "\n"
                   
        # Links to child directories
        if len(text_sub_dir) != 0:
            text = text + "\n## Subcategories \n"
            text = text + text_sub_dir
            
        if self.FORMAT != "markmap":
            text = text + "# Categories :  \n"
            
        text = self.content_struct_to_text(text, content, self.dest)
        
        if self.FORMAT != "markmap":
            text = text + self.add_associated_files(files)
            
        # Determine summary filename based on format
        summaryFilename = ""
        if self.FORMAT == "md" or self.FORMAT == "web":
            summaryFilename = "summary.md"
        elif self.FORMAT == "markmap":
            summaryFilename = "index.html"
        else:
            if self.dest.endswith('/'):
                dir_parts = self.dest.rstrip('/').split("/")
                summaryFilename = dir_parts[-1] + ".md" if dir_parts else "index.md"
            else:
                summaryFilename = path.basename(self.dest) + ".md"
                
        # Write summary file
        try:
            with open(self.dest+summaryFilename, 'w') as wfile:
                wfile.write(text)
        except Exception as e:
            print(f"Error writing summary file {self.dest+summaryFilename}: {e}")


    def generate_dir_summary(self):
        # Only proceed if source directory exists
        if not exists(self.src) or not isdir(self.src):
            print(f"Warning: Cannot generate summary for non-existent directory: {self.src}")
            return
            
        try:
            files = self.get_files()
            content = self.get_content_struct() 
            file_list = []
            
            # Process each file
            for cfile in files:
                try:
                    if cfile[-3:] == ".md":
                        markdown_getter = MarkdownGetter(self.FORMAT, self.src, self.dir_to_exclude, self.mainTags, self.real_path) 
                        markdown_writter = MarkdownWritter(self.FORMAT, self.dest, self.ROOT_DEST, self.mainTags, self.real_path)
                        markdown_writter.process_markdown_file(cfile, content, markdown_getter)
                    elif cfile[-5:] == ".adoc" and cfile.lower() != "summary.adoc":
                        asciidocGetter = AsciidocGetter(self.FORMAT, self.src, self.dir_to_exclude, self.mainTags, self.real_path)
                        asciidocWritter = AsciidocWritter(self.FORMAT, self.dest, self.ROOT_DEST, self.mainTags, self.real_path)
                        asciidocWritter.process_asciidoc_file(cfile, content, asciidocGetter)
                    else:
                        dest = self.dest+cfile.replace(" ","-")
                        if not path.isfile(dest):
                            is_ignored = False
                            for ignnore_type in [".swp",".swx", "swpx"]:
                                if dest.endswith(ignnore_type):
                                    is_ignored=True
                            if not is_ignored:
                                source_file = join(self.src, cfile)
                                if exists(source_file) and isfile(source_file):
                                    shutil.copy(source_file, dest)
                                else:
                                    print(f"Warning: Source file does not exist: {source_file}")
                    file_list.append(cfile)
                except Exception as e:
                    print(f"Error processing file {cfile}: {e}")
                    continue
                    
            # Generate summary content based on format
            if self.FORMAT == "web":
                self.FORMAT = "markmap"
                self.generate_dir_summary_content(content, files)
                self.FORMAT = "md"
                self.generate_dir_summary_content(content, files)
                self.FORMAT = "web"
            else:
                self.generate_dir_summary_content(content, files)
                
        except Exception as e:
            print(f"Error generating directory summary for {self.src}: {e}")
            traceback.print_exc()
