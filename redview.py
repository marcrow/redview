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
import yaml
import textwrap

# npm init -y; npm install express showdown fs path dotenv; node server.js

#------------------------Read and parse markdown
class MarkdownGetter:
    def __init__(self, FORMAT : str, src : str, dir_to_exclude : list, mainTags : list):
        self.FORMAT = FORMAT
        self.src = src
        self.dir_to_exclude = dir_to_exclude
        self.mainTags = mainTags
        self.category_keyword = self.get_category_keyword()[1:]
        

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
        categories = self.mainTags[0][self.category_keyword]
        return categories[number]

    def generate_summary(self, file_path, cfile, phases):
        """
        Génère un sommaire à partir d'un fichier Markdown.
        """
        with open(file_path, 'r') as file:
            lines = file.readlines()
        ignore=False
        summary = []
        current_titles = {1: None, 2: None, 3: None}  # Titres de niveau 1, 2 et 3 en cours
        current_level = 0  # Niveau du titre en cours

        for line_index, line in enumerate(lines):
            line = line.strip()
            if "```" in line:
                ignore = not ignore
            if ignore:
                continue
            if re.match(r'^#{1,4} .+', line):
                level = len(line.split()[0])
                title = line[2:]
                tags = []

                # Vérifier la ligne en dessous du titre de niveau 1
                if line_index < len(lines) - 1:
                    next_line = lines[line_index + 1].strip().lower()
                    tags = self.get_title_phase(next_line)
                    phases = tags + phases

                if level == 1:
                    current_titles[1] = (title, tags, [])
                    summary.append(current_titles[1])
                    current_level = 1
                elif level > 1 and level <= current_level + 1:
                    current_titles[level] = (title, tags, [])
                    current_titles[level - 1][2].append(current_titles[level])
                    current_level = level
        result = self.render_summary(summary, 0, cfile)
        result ="__Summary :__  \n" + result
        return result

    def render_summary(self,summary, title_level, cfile):
        result = ""
        if len(summary) == 0:
            return ""
        if len(summary[0]) == 2:
            for title, tag in summary:
                if self.FORMAT == "markmap":
                    result = result  + "#"*title_level+1 + title.replace("#", "") + "\n"     
                else:
                    result = result + title_level*"\t" + "- " +self.internal_link(title.replace("#", ""), cfile, title.replace("#", "")) + "\n"
        else :
            for title, tag, subtitles in summary:
                if self.FORMAT == "markmap":
                    result = result  + title + "\n"     
                else:
                    test = self.internal_link(title.replace("#", ""), cfile, title.replace("#", ""))
                    result = result + title_level*"\t" + "- "+ str(title_level +1 ) +". " +self.internal_link(title.replace("#", ""), cfile, title.replace("#", "")) + "\n"
                result = result + self.render_summary(subtitles, title_level + 1, cfile)
        return result
    
    def get_files(self):
        return [f for f in listdir(self.src) if isfile(join(self.src, f))]

    def get_directories(self):
        directories = [f for f in listdir(self.src) if not isfile(join(self.src, f))]
        return [item for item in directories if not (item.startswith("."))]
    
    def build_title_structure(self, titles):
        title_structure = []
        
        for level, title in titles:
            title = title.strip()
            if level == 1:
                title_structure.append({title: []})
                current_level_1 = title_structure[-1][title]
            elif level == 2:
                if current_level_1 is not None:
                    current_level_1.append({title: []})
                    current_level_2 = current_level_1[-1][title]
                else:
                    raise ValueError(f"Invalid structure: title '{title}' of level 2 does not depend on a title of level 1")
            elif level == 3:
                if current_level_2 is not None:
                    current_level_2.append(title)
                else:
                    raise ValueError(f"Invalid structure: title '{title}' of level 3 does not depend on a title of level 2")
        return title_structure
    
    def internal_link(self, text, destination, header):
        if self.FORMAT == "md":
            return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+replace_fr_char("".join(header.lower().rstrip().lstrip()).replace(" ","-").replace("(","").replace(")",""))+")  "
        elif self.FORMAT == "obsidian":
            return "[[#"+header[1:].replace("\n","")+"]]"
        elif self.FORMAT == "markmap":
            #destination = destination.replace(".md", ".html")
            return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip()).replace(" ","-")+")  "


    @staticmethod
    #Separate yaml from markdown 
    def parse_markdown_file(file_path):
        isYaml = False
        yaml = ""
        markdown_text = ""
        yamlEnd = 0
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if yamlEnd > 0:
                    markdown_text = "".join(lines[i-1:])
                    yaml = "".join(lines[:yamlEnd-1])
                    break
                if line == "":
                    continue
                elif isYaml:
                    yaml = yaml + line 
                    if line.strip() == "---":
                        
                        isYaml = False
                elif line.strip() == "---":
                        yaml = yaml + line
                        isYaml = True
                else:
                    yamlEnd = i+1
        if yamlEnd == 0:
            yaml =""
            markdown_text = "".join(lines)
        markdown_text = markdown_text.replace(yaml,'')
        return yaml, markdown_text

    def get_title_phase(self,line):
        keyword = "#"+self.get_category_keyword()
        phases = []
        if keyword+":" in line.lower() or keyword+":" in line.lower():
                p = line.replace(" ","").replace("\n","").split(":")[-1]
                phases = p.split(",")
        return phases

    def extract_phase(self,markdown_text, titles):
        phase = {}
        keyword = "#"+self.get_category_keyword()
        lines = markdown_text.split('\n')
        last_tags = []
        for index, line in enumerate(lines):
            previous_line = lines[index - 1].strip().lower()
            match = re.match(r'^(#+)\s+(.*)', previous_line)
            if match:
                current_title = match.group(2)
                for title1 in titles: #######! retourne que le premier élément 
                    for title in title1.keys():
                        if title.lower() == current_title.lower():
                            current_title = title
                            continue
                if keyword in line.lower() or keyword+"s" in line.lower():
                    tags = self.get_title_phase(line)
                    last_tags = tags
                    for tag in tags:
                        if phase.get(tag) is None:
                            phase[tag]=[]
                        phase[tag].append(current_title)

                elif re.match(r'^# (.+)$', previous_line): # title level 1
                    if len(phase) == 0: # Tag is missing on the first title 1
                        if phase.get("-1") is None:
                                phase["-1"]=[]
                        phase["-1"].append(current_title)
                    else: # ex : title 1 without tag 
                        for tag in last_tags:
                            if phase.get(tag) is None:
                                phase[tag]=[]
                            phase[tag].append(current_title)
        return phase

    def extract_titles(self, markdown_text):
        titles = []
        
        lines = markdown_text.split('\n')
        
        for index, line in enumerate(lines):
            match = re.match(r'^(#+)\s+(.*)', line)
            if match:
                level = len(match.group(1))
                title = match.group(2)
                titles.append((level, title))
                
        
        return titles

class MarkdownWritter:
    def __init__(self, FORMAT : str, dest : str, mainTags : list, child_dir : list):
        self.FORMAT = FORMAT
        self.ROOT_DEST = dest
        self.dest = dest
        self.mainTags = mainTags
        self.child_dir = child_dir
        self.category_keyword = self.get_category_keyword()
        
    
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
                #print(list(self.mainTags.keys())[0])
                #print(self.mainTags[list(self.mainTags.keys())[0]])
        else:
            print("La structure 'main' n'a pas été trouvée dans le fichier YAML.")
    
    def get_category(self,number):
        categories = {}
        categories = self.mainTags[0][self.category_keyword]
        return categories[number]

    def get_content_struct(self):
        content_struct = dict(self.mainTags[0][self.category_keyword])
        for k in content_struct.keys():
            content_struct[k]={}
        return content_struct

    def remove_tag(self, text):
        text =text.replace("#"+self.category_keyword,"")
        return text

    def add_associated_files(self, files):
        text = "# Associated files\n"
        if self.FORMAT == "markmap":
            text = "## Associated files\n"
        for f in files:
            f = f.replace(" ","-") 
            if f == "index.html" or f.lower() == "readme.md": 
                continue
            line = "- ["+f+"]"+"(./"+f+"), \n"
            if self.FORMAT=="markmap" and f[-3:] == ".md": # Use to stay on markmap preview if a md file is open
                if (path.exists(self.dest+f.replace(".md",".html"))):
                    print(self.dest+f.replace(".md",".html"))
                    line = "- ["+f+"]"+"(./"+f.replace(".md",".html")+"), \n"
            text = text + line
        return text

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
                return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip()).replace(" ","-")+")  "
            else:
                return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip())+")  "


    def generate_readme(self, markdown_getter):
        markdown_getter.src = clean_end_path(markdown_getter.src)
        self.dest = clean_end_path(self.dest)
        files = markdown_getter.get_files()
        content=self.get_content_struct()
        file_list = []
        summary=""
        yaml = ""
        markdown_text = ""
        text_sub_dir = self.create_sub_dir()
        for cfile in files :
            phases=[]
            ocfile = cfile
            file_list.append(cfile)
            if cfile[-3:] == ".md" and cfile.lower() != "readme.md":
                cfile = cfile.replace(" ", "-")
                summary = markdown_getter.generate_summary(markdown_getter.src+ocfile, cfile, phases) # and get phase
                yaml, markdown_text = markdown_getter.parse_markdown_file(markdown_getter.src+ocfile)
                titles = markdown_getter.extract_titles(markdown_text)
                file_content = markdown_getter.build_title_structure(titles)
                phases = markdown_getter.extract_phase(markdown_text, file_content)
                add_phase_in_content(phases, file_content, ocfile, content)
                #summary = generate_table_of_contents(content)

            if cfile[0] != "." or cfile == ".env" and cfile.lower() != "readme.md":
                if cfile[-2:] == "md":
                    if self.FORMAT == "markmap":
                        cfile = cfile[:-2] + "html"
                    with open(self.dest+cfile, "w") as df:
                        if self.FORMAT == "markmap":
                            with open(path.dirname(path.realpath(__file__))+"/export/web/ressources/template.html", "r") as tf: 
                                for line in tf:          
                                    df.write(line)
                        df.write(yaml)
                        df.write(summary)
                        markdown_text = self.remove_tag(markdown_text)
                        df.write(markdown_text)
                        # shall be done in parse_markdown_file
                        # with open(markdown_getter.src+ocfile, "r") as sf:
                        #     for line in sf:
                        #         if self.FORMAT == "obsidian":
                        #             if "#phase:" in line.lower() or "#phases:" in line.lower():
                        #                 phases=line.split(":")[-1]
                        #                 phases = phases.split(",")
                        #                 for phase in phases:
                        #                     df.write("#Phase"+phase)
                        #             else:
                        #                 df.write(line)
                        #         elif self.FORMAT == "markmap":
                        #             if "#phase:" in line.lower() or "#phases:" in line.lower():
                        #                 continue
                        #         else:
                        #             df.write(line)
                        if self.FORMAT == "markmap":
                            df.write("</script></div></body></html>")
                else:
                    shutil.copy(markdown_getter.src+ocfile, self.dest+cfile)

        text = "" 
        if self.FORMAT == "markmap":
            with open(path.dirname(path.realpath(__file__))+"/export/web/ressources/template.html", "r") as tf: 
                for line in tf:          
                    text = text + line
        fileName = self.dest.split("/")
        text =text + "# "+self.dest.split("/")[-2].capitalize()+"\n"           
        #Lien vers les réperoires enfants
        if len(text_sub_dir) != 0:
            text = text + "\n## Subcategories \n"
            text = text + text_sub_dir
        if self.FORMAT != "markmap":
            text = text + "# Categories :  \n"
        text = self.add_file_in_readme(text,content,self.dest)
        if self.FORMAT != "markmap":
            text = text + self.add_associated_files(files)
        summaryFilename = ""
        if self.FORMAT == "md":
            summaryFilename = "Readme.md"
        elif self.FORMAT == "markmap":
            summaryFilename = "index.html"
        else:
            if self.dest[-1]=="/":
                summaryFilename = self.dest.split("/")[-2] + ".md"
            else:
                summaryFilename = self.dest.split("/")[-1] + ".md"
        with open(self.dest+summaryFilename,'w') as wfile:
            wfile.write(text)

    
    def add_file_in_readme(self, text, content, dpath, level=0):
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
                        #text = add_file_in_readme(text, content[k][elt],  dpath+"/"+elt, level)
                        text = self.add_file_in_readme(text, content[k][elt],  "./"+elt, level +1)
                else:
                    #h1 and h2
                    tlevel = level-2
                    h= ""
                    if level == 1:
                        h = "### "+icon_title
                    else:
                        h = "\t"*tlevel
                        h = h +"- "+icon_chapter
                    
                    text= text +h+ self.format_link(k,dpath,k) +"  \n"
                    for elt in v:
                        text = self.add_file_in_readme(text, elt,  dpath, level+1)
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
                        text = self.add_file_in_readme(text, elt,  dpath, level+1)
                    else:
                        text= text +h+" "+icon_chapter+ self.format_link(elt,dpath,elt) +"  \n"
        return text

    # Create subdirectories based on child_dir from self().
    # Return text with links to all subdirectories
    def create_sub_dir(self):
        text = ""
        for directory in self.child_dir:
            directory = directory.replace(" ","_")
            if not path.exists(self.dest+directory):
                mkdir(self.dest+directory)
            # title = "["+Directory+"]("+path+directory+"/)"
            if self.FORMAT == "markmap":
                text = text + "- " + self.format_link(directory,"./"+directory+"/index.html")+"  \n"
            elif self.FORMAT == "md":
                text = text + "- 📁 " + self.format_link(directory,self.dest+directory+"/")+"  \n"
            elif self.FORMAT == "obsidian":
                text = text + "- " + self.format_link(directory,"./"+directory+"/"+directory+".md") + "  \n"
            
        return text

    def generate_markmap_readme(self, markdown_getter):
        markdown_getter.src = clean_end_path(markdown_getter.src)
        files = [f for f in listdir(markdown_getter.src) if isfile(join(markdown_getter.src, f))]
        content=self.get_content_struct()
        file_list = []
        text_sub_dir = self.create_sub_dir()
        for cfile in files :
            phases = []
            summary = ""
            ocfile = cfile
            file_list.append(cfile)
            if cfile[-3:] == ".md" and cfile.lower() != "readme.md":
                cfile = cfile.replace(" ", "-")
                #summary = extract_from_file(markdown_getter.src, cfile,content)
                summary = markdown_getter.generate_summary(markdown_getter.src+ocfile, cfile, phases) # and get phase
                yaml, markdown_text = markdown_getter.parse_markdown_file(markdown_getter.src+ocfile)
                titles = markdown_getter.extract_titles(markdown_text)
                file_content = markdown_getter.build_title_structure(titles)
                phases = markdown_getter.extract_phase(markdown_text, file_content)
                add_phase_in_content(phases, file_content, ocfile, content)
                
            if cfile[0] != "." in cfile and cfile.lower() != "readme.md":
                if cfile[-2:] == "md":
                    if self.FORMAT == "markmap":
                        cfile = cfile[:-2] + "html"
                    with open(self.dest+cfile, "w") as df:
                        with open(path.dirname(path.realpath(__file__))+"/export/web/ressources/template.html", "r") as tf: 
                            for line in tf:          
                                df.write(line)
                        df.write(yaml)
                        #df.write(summary)
                        markdown_text = self.remove_tag(markdown_text)
                        df.write(markdown_text)
                        df.write("</script></div></body></html>")
                else:
                    shutil.copy(markdown_getter.src+ocfile, self.dest+cfile)

        text = "" 
        if self.FORMAT == "markmap":
            with open(path.dirname(path.realpath(__file__))+"/export/web/ressources/template.html", "r") as tf: 
                for line in tf:          
                    text = text + line
        fileName = self.dest.split("/")
        text =text + "# "+self.dest.split("/")[-2].capitalize()+"\n"           
        #text = text + "\n # Sous Catégories  \n"
        #Lien vers les réperoires enfants
        if len(text_sub_dir) != 0:
            text = text + "\n## Sous Catégories  \n"
            text = text + text_sub_dir
        text = text +self.add_associated_files(file_list)

        text = self.add_file_in_readme(text,content,self.dest)
        summaryFilename = ""
        summaryFilename = "index.html"
        with open(self.dest+summaryFilename,'w') as wfile:
            wfile.write(text)

class RedviewGenerator:
    def __init__(self, FORMAT : str, src : str, dest : str, script_dir : str, dir_to_exclude : list, mainTags : list):
        self.script_dir = script_dir
        self.dir_to_exclude = dir_to_exclude
        self.markdown_getter = MarkdownGetter(FORMAT, src , dir_to_exclude , mainTags) 
        self.markdown_writter = MarkdownWritter(FORMAT, dest, mainTags, self.get_directories())
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
def replace_fr_char(text):
    replacements = {
        'é' : '233',
        'à' : '224',
        'è' : '232'
    }
    for old, new in replacements.items():
        text = text.replace(old,new)
        
    return text

def add_phase_in_content(phases, files_content, cfile, content):
    for tag, titles in phases.items():
        tag = tag
        for title in titles:
            title1 = {}
            for index,  tmp_title in enumerate(files_content): #retrieve level1 title  
                if list(tmp_title.keys())[0] == title:
                    title1 = files_content[index]
            if cfile not in content[tag]:
                content[tag][cfile]=title1
            else:
                content[tag][cfile].update(title1)



def clean_end_path(path):
        if path[-1] != "/":
            return  path + "/"
        elif path[-2] == "/":
            return path[:-1]
        return path

def extract_yaml_conf(yaml_file):
    with open(yaml_file, 'r') as file:
        return yaml.safe_load(file)


def getMainTags(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        
        if 'main' in data.get('tag'):
            main_structure = data['tag']['main']
            for index, element in enumerate(main_structure) :
                main_structure[index] = {k.lower(): v for k, v in main_structure[index].items()} # Lower all keys
            return main_structure
        
        return None

        

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

    dir_to_exclude = ["ressources",".git","node"]
    script_dir = path.dirname(path.realpath(__file__))

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