from os import mkdir
from os import path
from os import listdir
import shutil
import re
from os.path import isfile, join
import yaml
from src.utils import *



# npm init -y; npm install express showdown fs path dotenv; node server.js

#------------------------Read and parse asciidoc
class AsciidocGetter:
    def __init__(self, FORMAT : str, src : str, dir_to_exclude : list, mainTags : list, realpath : str):
        self.FORMAT = FORMAT
        self.src = src
        self.dir_to_exclude = dir_to_exclude
        self.mainTags = mainTags
        self.category_keyword = self.get_category_keyword()[1:]
        self.realpath = realpath
    

        

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
    

    
    def add_new_title(self, level, title, cfile, title_structure, current_level_1, current_level_2):
        if level == 1:
                title_structure.append({title: []})
                current_level_1 = title_structure[-1][title]            
        elif level == 2:
            if current_level_1 is None:
                print(f"Warning - Invalid structure: in {cfile}, '{title}' is a level 2 title wich does not depend on a title of level 1. File name add as title 1.")
                title_structure, current_level_1, current_level_2 = self.add_new_title(1, cfile.replace(".adoc",""), cfile, title_structure, current_level_1, current_level_2)
            current_level_1.append({title: []})
            current_level_2 = current_level_1[-1][title]

        elif level == 3:
            if current_level_1 is None:
                print(f"Warning - Invalid structure: in {cfile}, '{title}' is a level 2 title wich does not depend on a title of level 1. File name add as title 1.")
                title_structure, current_level_1, current_level_2 = self.add_new_title(1, cfile.replace(".adoc",""), cfile, title_structure, current_level_1, current_level_2)
            if current_level_2 is None:
                print(f"Warning - Invalid structure: in {cfile}, '{title}' is a level 3 title wich does not depend on a title of level 2. Transform level 3 to level 2 title.")
                current_level_1.append({title: []})
                current_level_2 = current_level_1[-1][title]
            else:
                current_level_2.append(title)
        return title_structure, current_level_1, current_level_2
    
    def build_title_structure(self, titles, cfile):
        title_structure = []
        current_level_1 = None
        current_level_2 = None
        for level, title in titles:
            title = title.strip()
            title_structure, current_level_1, current_level_2 = self.add_new_title(level, title, cfile, title_structure, current_level_1, current_level_2)
            
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
    #Separate yaml from asciidoc 
    def parse_asciidoc_file(file_path):
        isYaml = False
        yaml = ""
        asciidoc_text = ""
        yamlEnd = 0
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if yamlEnd > 0:
                    asciidoc_text = "".join(lines[i-1:])
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
            asciidoc_text = "".join(lines)
        asciidoc_text = asciidoc_text.replace(yaml,'')
        return yaml, asciidoc_text

    def get_title_phase(self,line):
        keyword = ":"+self.get_category_keyword()+":"
        phases = []
        line = line.lower().strip()
        if line.startswith(keyword):
                line = line.replace(keyword,"")
                p = line.replace("\n","")
                pattern = f"{re.escape(' ')}|{re.escape(',')}" # extract tag via , or space delimeter
                phases = re.split(pattern, p) 
        return [x for x in phases if x] 

    def getNextTag(self, lines, index):
        keyword = ":"+self.get_category_keyword()+":"
        for i, line in enumerate(lines[index+1:]):
            if keyword in line.lower():
                return self.get_title_phase(line)
            if line.startswith("="):
                return []
        return []

    def extract_phase(self,asciidoc_text, titles):
        phase = {}
        lines = asciidoc_text.split('\n')
        last_tags = []
        for index, line in enumerate(lines):
            match = re.match(r'^(=+)\s+(.*)', line)
            if match:
                current_title = match.group(2)
                for title1 in titles: #######! retourne que le premier élément 
                    for title in title1.keys():
                        if title.lower() == current_title.lower():
                            current_title = title
                            continue
                tags = self.getNextTag(lines, index)

                if len(tags)>0:
                    last_tags = tags
                    for tag in tags:
                        if phase.get(tag) is None:
                            phase[tag]=[]
                        phase[tag].append(current_title)

                elif re.match(r'^= (.+)$', line): # title level 1
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

    def extract_titles(self, asciidoc_text):
        titles = []
        is_code= False
        lines = asciidoc_text.split('\n')
        
        for index, line in enumerate(lines):
            match = re.match(r'^(=+)\s+(.*)', line)
            if line.startswith("```"):
                is_code= not is_code
            if is_code:
                continue
            if match:
                level = len(match.group(1))
                title = match.group(2)
                titles.append((level, title))
                
        
        return titles

class AsciidocWritter:
    def __init__(self, FORMAT : str, dest : str, ROOT_DEST : str, mainTags : list, realpath : str):
        self.FORMAT = FORMAT
        self.ROOT_DEST = dest
        self.dest = dest
        self.mainTags = mainTags
        self.category_keyword = self.get_category_keyword()
        self.realpath = realpath
        
    
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
    
    def process_asciidoc_file(self, cfile, content, asciidoc_getter):
        phases=[]
        yaml = ""
        asciidoc_text = ""
        ocfile = cfile
        #For summary file, if it's possible rename them as the directory name
        if cfile.lower() == "summary.md" :
            return
            # cfile = path.basename(path.dirname(asciidoc_getter.src)) + ".md"
            # if path.isfile(asciidoc_getter.src+cfile):
            #     return
        cfile = cfile.replace(" ", "-")
        
        yaml, asciidoc_text = asciidoc_getter.parse_asciidoc_file(asciidoc_getter.src+ocfile)
        titles = asciidoc_getter.extract_titles(asciidoc_text)
        file_content = asciidoc_getter.build_title_structure(titles, cfile)
        phases = asciidoc_getter.extract_phase(asciidoc_text, file_content)
        add_phase_in_content(phases, file_content, cfile, content)

        try:
            shutil.copy(asciidoc_getter.src+ocfile, self.dest+cfile)
        except shutil.SameFileError:
            print(self.dest+cfile+" File already exists")
            pass
        except Exception as e:
            print("Issue ignored for "+self.dest+cfile + " : "+e)
            pass


