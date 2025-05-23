import shutil
import re
from src.ascii_redview import AsciidocGetter, AsciidocWritter
from src.utils import *
from os import symlink
from os import path


# npm init -y; npm install express showdown fs path dotenv; node server.js

#------------------------Read and parse markdown
class MarkdownGetter:
    def __init__(self, FORMAT : str, src : str, dir_to_exclude : list, mainTags : list, realpath : str):
        self.FORMAT = FORMAT
        self.src = clean_end_path(src)
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

    def cloneAsciiGetter(self):
        return AsciidocGetter( self.FORMAT, self.src, self.dir_to_exclude, self.mainTags, self.realpath)

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


    def add_new_title(self, level, title, cfile, title_structure, current_level_1, current_level_2):
        if level == 1:
                title_structure.append({title: []})
                current_level_1 = title_structure[-1][title]            
        elif level == 2:
            if current_level_1 is None:
                print(f"Warning - Invalid structure: in {cfile}, '{title}' is a level 2 title wich does not depend on a title of level 1. File name add as title 1.")
                title_structure, current_level_1, current_level_2 = self.add_new_title(1, cfile.replace(".md",""), cfile, title_structure, current_level_1, current_level_2)
            current_level_1.append({title: []})
            current_level_2 = current_level_1[-1][title]

        elif level == 3:
            if current_level_1 is None:
                print(f"Warning - Invalid structure: in {cfile}, '{title}' is a level 2 title wich does not depend on a title of level 1. File name add as title 1.")
                title_structure, current_level_1, current_level_2 = self.add_new_title(1, cfile.replace(".md",""), cfile, title_structure, current_level_1, current_level_2)
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
        else:
            return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+replace_fr_char("".join(header.lower().rstrip().lstrip()).replace(" ","-").replace("(","").replace(")",""))+")  "


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
        level1_titles = set()
        
        for index, line in enumerate(lines):
            previous_line = lines[index - 1].strip().lower() if index > 0 else ""
            match = re.match(r'^(#+)\s+(.*)', previous_line)
            if match:
                current_title = match.group(2)
                level = len(match.group(1))
                
                for title1 in titles: #######! retourne que le premier élément 
                    for title in title1.keys():
                        if title.lower() == current_title.lower():
                            current_title = title
                            continue
                
                # Track all level 1 titles
                if level == 1:
                    level1_titles.add(current_title)
                
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
        
        # Ensure all level 1 titles without explicit tags are in phase["-1"]
        if phase.get("-1") is None:
            phase["-1"] = []
            
        # Find all level 1 titles that aren't in any phase yet
        all_tagged_titles = set()
        for tag_titles in phase.values():
            all_tagged_titles.update(tag_titles)
            
        for title in level1_titles:
            if title not in all_tagged_titles:
                phase["-1"].append(title)
                
        return phase


    def extract_titles(self, markdown_text):
        titles = []
        
        lines = markdown_text.split('\n')
        is_code= False
        
        for index, line in enumerate(lines):
            match = re.match(r'^(#+)\s+(.*)', line)
            if line.startswith("```"):
                is_code= not is_code
            if is_code:
                continue
            if match:
                level = len(match.group(1))
                title = match.group(2)
                titles.append((level, title))
            
        
        return titles



class MarkdownWritter:
    def __init__(self, FORMAT : str, dest : str, ROOT_DEST  : str,  mainTags : list, realpath : str):
        self.FORMAT = FORMAT
        self.ROOT_DEST = dest
        self.dest = clean_end_path(dest)
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
    
    def cloneAsciiWritter(self):
        return AsciidocWritter(self.FORMAT, self.dest, self.mainTags, self.realpath)

    def remove_tag(self, text):
        text =text.replace("#"+self.category_keyword,"")
        return text

    
    def process_markdown_file(self, cfile, content, markdown_getter):
        phases=[]
        #summary=""
        yaml = ""
        markdown_text = ""
        ocfile = cfile
        cfile = cfile.replace(" ", "-")
        #For summary file, if it's possible rename them as the directory name
        if cfile.lower() == "summary.md" :
            return
            # cfile = path.basename(path.dirname(markdown_getter.src)) + ".md"
            # if path.isfile(markdown_getter.src+cfile):
            #     return
        #summary = markdown_getter.generate_summary(markdown_getter.src+ocfile, cfile, phases) # and get phase
        yaml, markdown_text = markdown_getter.parse_markdown_file(markdown_getter.src+ocfile)
        titles = markdown_getter.extract_titles(markdown_text)
        file_content = markdown_getter.build_title_structure(titles, cfile)
        phases = markdown_getter.extract_phase(markdown_text, file_content)
        add_phase_in_content(phases, file_content, cfile, content)


        # Removed to simplify the web usage in docker - need to be update to be used with without web interface
        # if cfile[-2:] == "md": #generate markmap file
        #     if self.FORMAT == "markmap":
        #         cfile = cfile[:-2] + "html"
        #     with open(self.dest+cfile, "w") as df:
        #         if self.FORMAT == "markmap":
        #             with open(self.realpath+"/export/web/ressources/template.html", "r") as tf: 
        #                 for line in tf:          
        #                     df.write(line)
        #         df.write(yaml)
        #         if self.FORMAT != "markmap":
        #             df.write(summary)
        #         markdown_text = self.remove_tag(markdown_text)
        #         df.write(markdown_text)
        #         if self.FORMAT == "markmap":
        #             df.write("</script></div><span id='source' hidden='hidden'>.md</span></body></html>")
        
        try:
            target = markdown_getter.src+ocfile
            location = self.dest+cfile
            if not path.exists(target) :
                symlink(target,location)
        except FileExistsError:
            print(location  +" FileExistsError -> skipped")
            return
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            return 

        # try:
        #     shutil.copy(markdown_getter.src+ocfile, self.dest+cfile)
        # except shutil.SameFileError:
        #     print(self.dest+cfile+" File already exists")
        #     pass
        # except Exception as e:
        #     print("Issue ignored for "+self.dest+cfile + " : "+e)
        #     pass
