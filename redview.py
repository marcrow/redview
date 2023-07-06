#!/usr/bin/python3

from os import mkdir
from os import rmdir
from os import path
from os import listdir
from shutil import rmtree
import shutil
import re
from os.path import isfile, join
import argparse
import yaml

# npm init -y; npm install express showdown fs path dotenv; node server.js



def getMainTags(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        
        if 'main' in data['tag']:
            main_structure = data['tag']['main']
            return main_structure
        
        return None

def get_category_keyword():
    categories = {}
    if mainTags is not None:
        if len(mainTags) != 1 :
            print("Error : In conf.yaml, only one main tag is authorized")
            exit()
        if isinstance(mainTags, list):
            if isinstance(mainTags[0], dict):
                tag = list(mainTags[0].keys())[0]
                return "#"+tag.lower()
            else:
                print( "Error : custom tag in main shall be in a dir structure in conf.yaml")
                exit()
        else:
            print( "Error : main tag shall be in a list in conf.yaml")
            exit()
            #print(list(mainTags.keys())[0])
            #print(mainTags[list(mainTags.keys())[0]])
    else:
        print("La structure 'main' n'a pas été trouvée dans le fichier YAML.")

def get_category(number):
    categories = {}
    if mainTags is not None:
        if len(mainTags) != 1 :
            print("Error : In conf.yaml, only one main tag is authorized")
            exit()
        if isinstance(mainTags, list):
            if isinstance(mainTags[0], dict):
                tag = list(mainTags[0].keys())[0]
                categories = mainTags[0][tag]
            else:
                print( "Error : custom tag in main shall be in a dir structure in conf.yaml")
                exit()
        else:
            print( "Error : main tag shall be in a list in conf.yaml")
            exit()
            #print(list(mainTags.keys())[0])
            #print(mainTags[list(mainTags.keys())[0]])
    else:
        print("La structure 'main' n'a pas été trouvée dans le fichier YAML.")
    return categories[number]

def replace_fr_char(text):
    replacements = {
        'é' : '233',
        'à' : '224',
        'è' : '232'
    }
    for old, new in replacements.items():
        text = text.replace(old,new)
        
    return text

def format_link(text, destination, header = ""):
    destination = destination.replace(dest,"")
    if len(header) == 0:
        return "["+text.replace("_"," ").replace("\n","")+"]("+destination.replace("\n","")+")  "
    else:
        if FORMAT == "md":
            return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+replace_fr_char("".join(header.lower().rstrip().lstrip()).replace(" ","-").replace("(","").replace(")",""))+")  "
        elif FORMAT == "obsidian":
            return "[["+destination.replace("\n","")+"#"+header.replace("\n","")+"]]"
        if FORMAT == "markmap":
            destination = destination.replace(".md", ".html")
            return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip()).replace(" ","-")+")  "
        else:
            return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip())+")  "

def internal_link(text, destination, header):
    if FORMAT == "md":
        return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+replace_fr_char("".join(header.lower().rstrip().lstrip()).replace(" ","-").replace("(","").replace(")",""))+")  "
    elif FORMAT == "obsidian":
        return "[[#"+header[1:].replace("\n","")+"]]"
    elif FORMAT == "markmap":
        #destination = destination.replace(".md", ".html")
        return "["+text.replace("\n","")+"]("+destination.replace("\n","")+"#"+"".join(header.lower().rstrip().lstrip()).replace(" ","-")+")  "


def add_file_in_readme(text, content, dpath, level=0):
    # print(content)
    icon_title = ":closed_book: "
    icon_chapter = ":bookmark: "
    icon_phase = ":page_facing_up: "
    if FORMAT == "markmap":
        icon_title = ""
        icon_chapter = ""
        icon_phase = ""
    if isinstance(content,dict):
        for k,v in content.items():
            #Phase
            if level == 0:
                h = "##"
                if len(v) > 0:
                    text= text +h+" "+icon_phase+" "+ get_category(k) +"  \n"
                #Files
                for elt in v:
                    #For obsidian usage, test relative path
                    #text = add_file_in_readme(text, content[k][elt],  dpath+"/"+elt, level)
                    text = add_file_in_readme(text, content[k][elt],  "./"+elt, level +1)
            else:
                #h1 and h2
                tlevel = level-2
                h= ""
                if level == 1:
                    h = "### "+icon_title
                else:
                    h = "\t"*tlevel
                    h = h +"- "+icon_chapter
                
                text= text +h+ format_link(k,dpath,k) +"  \n"
                for elt in v:
                    text = add_file_in_readme(text, elt,  dpath, level+1)
    else: 
        #h3 
        tlevel = level-2
        h = "\t"*tlevel
        h = h +"-"
        if isinstance(content, str):
            text= text +h+" "+icon_chapter+ format_link(content,dpath,content) +"  \n"
        else:
            for elt in content:
                if isinstance(elt, dict):
                     text = add_file_in_readme(text, elt,  dpath, level+1)
                else:
                    text= text +h+" "+icon_chapter+ format_link(elt,dpath,elt) +"  \n"
    return text


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


def add_phase_in_content(phases, files_content, cfile, content):
    for tag, title in phases.items():
        tag = int(tag)
        title1 = {title :files_content[0].get(title)}
        print(title1)
        if cfile not in content[tag]:
            content[tag][cfile]=title1
        else:
            content[tag][cfile].append(title1)


def extract_phase(markdown_text, titles):
    phase = {}
    keyword = get_category_keyword()
    lines = markdown_text.split('\n')
    for index, line in enumerate(lines):
        if keyword in line.lower() or keyword+"s" in line.lower():
            tags = get_title_phase(line)
            previous_line = lines[index - 1].strip().lower()
            match = re.match(r'^(#+)\s+(.*)', previous_line)
            if match:
                current_title = match.group(2)
                for title in titles[0].keys():
                    if title.lower() == current_title.lower():
                        for tag in tags:
                            phase[tag]=title
    return phase



def extract_titles(markdown_text):
    titles = []
    
    lines = markdown_text.split('\n')
    
    for index, line in enumerate(lines):
        match = re.match(r'^(#+)\s+(.*)', line)
        if match:
            level = len(match.group(1))
            title = match.group(2)
            titles.append((level, title))
            
    
    return titles


def build_title_structure(titles):
    title_structure = []
    
    for level, title in titles:
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


def generate_table_of_contents(title_structure):
    table_of_contents = ''
    
    for item in title_structure:
        for title, children in item.items():
            table_of_contents += f"{'#' * (len(title)+1)} {title}\n"
            if children:
                for child in children:
                    if isinstance(child, dict):
                        for child_title, _ in child.items():
                            table_of_contents += f"{'#' * (len(title)+2)} {child_title}\n"
                    elif isinstance(child, list):
                        for child_title in child:
                            table_of_contents += f"{'#' * (len(title)+3)} {child_title}\n"
    
    return table_of_contents

def extract_from_file(spath, cfile,content):
    summary = ""
    phases = []
    keyword = get_category_keyword()
    with open(spath+cfile, "r") as f:
        cfile=cfile.replace(" ","_")
        titles=[]
        elt1 = {}
        elt2 = {}
        elt3 = []
        ignore=False
        parent1=""
        parent2 = ""
        #fw.write(":arrow_backward: <ins>*[Retour](..)* </ins> \n")
        for line in f:
            if keyword+"s:" not in line.lower() or keyword+":" not in line.lower():
                summary = summary + line
            #ignore test inside code
            if line[0:3] == "```":
                ignore = not ignore
            if ignore:
                continue

            if keyword+"s:" in line.lower() or keyword+":" in line.lower():
                p = line.replace(" ","").replace("\n","").split(":")[-1]
                phases = p.split(",")

            i = 0
            title_level = -1
            while line[i] == "#":
                title_level = title_level + 1
                i = i + 1
            #don't consider comment line or tag
            if line[i] != " ":
                title_level = -1

            if line[0:2] == "# ":
                if len(elt3) > 0:
                    if parent2 == "":
                        print("Erreur dans la documentation, "+str(elt3)+" ne dépends pas d'un titre 2")
                        exit()
                    elt2[parent2].append(elt3)
                    elt3=[]
                if len(elt2) > 0:
                    #print(elt1[parent1])
                    if parent1 == "":
                        print("Erreur dans la documentation, "+str(elt2)+" ne dépends pas d'un titre 1")
                    elt1[parent1].append(elt2)
                    elt2={}
                if len(elt1) > 0:
                    titles.append(elt1)
                    elt1={}
                    if len(phases) == 0:
                        phases.append(-1)
                    for phase in phases: 
                        phase = int(phase)
                        # print(cfile)
                        # print(phases)
                        if cfile not in content[phase]:
                            # print(content[phase])
                            content[phase][cfile] = titles
                        else:
                            content[phase][cfile].extend(titles)
                    titles = []
                elt1[line[2:]]=[]
                parent1 = line[2:]
            if line[0:3] == "## ":
                if len(elt3) > 0:
                    if parent2 == "":
                        print("Erreur dans la documentation, "+str(elt3)+" ne dépends pas d'un titre 2")
                        exit()
                    elt2[parent2].append(elt3)
                    elt3=[]
                if len(elt2) > 0:
                    if parent1 == "":
                        print("Erreur dans la documentation, "+str(elt2)+" ne dépends pas d'un titre 1")
                        exit()
                    elt1[parent1].append(elt2)
                    elt2={}
                elt2[line[3:]]=[]
                parent2=line[3:]
            if line[0:4] == "### ":
                if len(elt3) > 0:
                    elt2[parent2].append(elt3)
                    elt3=[]
                elt3.append(line[4:])
                #title = "["+line[2:]+"]("+dpath+cfile+"#"+line[2:].replace(" ","-").replace("\n","")+")"
                #title = "["+line[2:]+"]("+str(dpath)+str(cfile)+"#)"
        if len(elt3) > 0:
            if parent2 == "":
                print("Erreur dans la documentation, "+str(elt3)+" ne dépends pas d'un titre 2")
                exit()
            elt2[parent2].append(elt3)
            elt3={}
        if len(elt2) > 0:
            if parent1 == "":
                print("Erreur dans la documentation, "+str(elt2)+" ne dépends pas d'un titre 1")
                exit()
            #print(elt1[parent1])
            elt1[parent1].append(elt2)
            elt2={}
        if len(elt1) > 0:
            titles.append(elt1)
        if len(phases) == 0:
            phases.append(-1)
        for phase in phases: 
            phase = int(phase)
            # print(cfile)
            # print(phases)
            if cfile not in content[phase]:
                content[phase][cfile] = titles
            else:
                content[phase][cfile].extend(titles)
    return summary

def generate_markmap_readme(spath,dpath):
    if spath[-1] != "/":
        spath = spath + "/"
    if dpath[-1] != "/":
        dpath = dpath + "/"
    files = [f for f in listdir(spath) if isfile(join(spath, f))]
    directories = [f for f in listdir(spath) if not isfile(join(spath, f)) and not f in dir_to_exclude]
    directories = [item for item in directories if not item.startswith(".")]
    content={-1:{},0:{},1:{},2:{},3:{},4:{}}
    file_list = []
    for cfile in files :
        phases = []
        summary = ""
        ocfile = cfile
        if cfile[-3:] == ".md" and cfile.lower() != "readme.md":
            file_list.append(cfile)
            #summary = extract_from_file(spath, cfile,content)
            summary = generate_summary(spath+cfile, cfile, phases) # and get phase
            yaml, markdown_text = parse_markdown_file(spath+cfile)
            titles = extract_titles(markdown_text)
            file_content = build_title_structure(titles)
            phases = extract_phase(markdown_text, file_content)
            add_phase_in_content(phases, file_content, cfile, content)
        if cfile[0] != "." in cfile and cfile.lower() != "readme.md":
            if cfile[-2:] == "md":
                if FORMAT == "markmap":
                    cfile = cfile[:-2] + "html"
                with open(dpath+cfile, "w") as df:
                    with open("./export/web/ressources/template.html", "r") as tf: 
                        for line in tf:          
                            df.write(line)
                    df.write(yaml)
                    #df.write(summary)
                    df.write(markdown_text)
                    df.write("</script></div></body></html>")
            else:
                shutil.copy(spath+ocfile, dpath+cfile)

    text = "" 
    if FORMAT == "markmap":
        with open("./export/web/ressources/template.html", "r") as tf: 
            for line in tf:          
                text = text + line
    fileName = dpath.split("/")
    text =text + "# "+dpath.split("/")[-2].capitalize()+"\n"           
    #text = text + "\n # Sous Catégories  \n"
    tmptext = ""
    #Lien vers les réperoires enfants
    for directory in directories:
        if not path.exists(dpath+directory):
            mkdir(dpath+directory)
        # title = "["+Directory+"]("+path+directory+"/)"
        tmptext = tmptext + "- " + format_link(directory,"./"+directory+"/index.html")+"  \n"
    if len(tmptext) != 0:
        text = text + "\n## Sous Catégories  \n"
        text = text + tmptext
    text = add_file_in_readme(text,content,dpath)
    summaryFilename = ""
    summaryFilename = "index.html"
    with open(dpath+summaryFilename,'w') as wfile:
        wfile.write(text)
    return directories

def clean_end_path(path):
    if path[-1] != "/":
        return  path + "/"
    return path

def get_files(spath):
    return [f for f in listdir(spath) if isfile(join(spath, f))]

def get_directories(spath):
    directories = [f for f in listdir(spath) if not isfile(join(spath, f))]
    return [item for item in directories if not (item.startswith("."))]

def get_title_phase(line):
    keyword = get_category_keyword()
    phases = []
    if keyword+":" in line.lower() or keyword+":" in line.lower():
            p = line.replace(" ","").replace("\n","").split(":")[-1]
            phases = p.split(",")
    return phases

def render_summary(summary, title_level, cfile):
    result = ""
    if len(summary) == 0:
        return ""
    if len(summary[0]) == 2:
        for title, tag in summary:
            if FORMAT == "markmap":
                result = result  + "#"*title_level+1 + title.replace("#", "") + "\n"     
            else:
                result = result + title_level*"\t" + "- " +internal_link(title.replace("#", ""), cfile, title.replace("#", "")) + "\n"
    else :
        for title, tag, subtitles in summary:
            if FORMAT == "markmap":
                result = result  + title + "\n"     
            else:
                result = result + title_level*"\t" + "- "+ str(title_level +1 ) +". " +internal_link(title.replace("#", ""), cfile, title.replace("#", "")) + "\n"
            result = result + render_summary(subtitles, title_level + 1, cfile)
    return result


def generate_summary(file_path, cfile, phases):
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
                tags = get_title_phase(next_line)
                phases = tags + phases

            if level == 1:
                current_titles[1] = (title, tags, [])
                summary.append(current_titles[1])
                current_level = 1
            elif level > 1 and level <= current_level + 1:
                current_titles[level] = (title, tags, [])
                current_titles[level - 1][2].append(current_titles[level])
                current_level = level
    result = render_summary(summary, 0, cfile)
    result ="__Summary :__  \n" + result
    return result



def generate_readme(spath, dpath):
    spath = clean_end_path(spath)
    dpath = clean_end_path(dpath)
    files = get_files(spath)
    directories = get_directories(spath)
    content={-1:{},0:{},1:{},2:{},3:{},4:{}}
    file_list = []
    summary=""
    yaml = ""
    markdown_text = ""
    for cfile in files :
        phases=[]
        ocfile = cfile
        if cfile[-3:] == ".md" and cfile.lower() != "readme.md":
            file_list.append(cfile)
            summary = generate_summary(spath+cfile, cfile, phases) # and get phase
            yaml, markdown_text = parse_markdown_file(spath+cfile)
            titles = extract_titles(markdown_text)
            file_content = build_title_structure(titles)
            phases = extract_phase(markdown_text, file_content)
            add_phase_in_content(phases, file_content, cfile, content)
            #summary = generate_table_of_contents(content)

        if cfile[0] != "." or cfile == ".env" and cfile.lower() != "readme.md":
            if cfile[-2:] == "md":
                if FORMAT == "markmap":
                    cfile = cfile[:-2] + "html"
                with open(dpath+cfile, "w") as df:
                    if FORMAT == "markmap":
                        with open("./export/web/export/web/ressources/template.html", "r") as tf: 
                            for line in tf:          
                                df.write(line)
                    df.write(yaml)
                    df.write(summary)
                    df.write(markdown_text)
                    # shall be done in parse_markdown_file
                    # with open(spath+ocfile, "r") as sf:
                    #     for line in sf:
                    #         if FORMAT == "obsidian":
                    #             if "#phase:" in line.lower() or "#phases:" in line.lower():
                    #                 phases=line.split(":")[-1]
                    #                 phases = phases.split(",")
                    #                 for phase in phases:
                    #                     df.write("#Phase"+phase)
                    #             else:
                    #                 df.write(line)
                    #         elif FORMAT == "markmap":
                    #             if "#phase:" in line.lower() or "#phases:" in line.lower():
                    #                 continue
                    #         else:
                    #             df.write(line)
                    if FORMAT == "markmap":
                        df.write("</script></div></body></html>")
            else:
                shutil.copy(spath+ocfile, dpath+cfile)

    text = "" 
    if FORMAT == "markmap":
        with open("./export/web/export/web/ressources/template.html", "r") as tf: 
            for line in tf:          
                text = text + line
    fileName = dpath.split("/")
    text =text + "# "+dpath.split("/")[-2].capitalize()+"\n"           
    #text = text + "\n # Sous Catégories  \n"
    tmptext = ""
    #Lien vers les réperoires enfants
    for directory in directories:
        if not path.exists(dpath+directory):
            mkdir(dpath+directory)
        # title = "["+Directory+"]("+path+directory+"/)"
        if FORMAT == "md":
            tmptext = tmptext + "- :file_folder: " + format_link(directory,dpath+directory+"/")+"  \n"
        if FORMAT == "obsidian":
            tmptext = tmptext + "- " + format_link(directory,"./"+directory+"/"+directory+".md") + "  \n"
        if FORMAT == "markmap":
            tmptext = tmptext + "- " + format_link(directory,"./"+directory+"/index.html")+"  \n"
    if len(tmptext) != 0:
        text = text + "\n## Sous Catégories  \n"
        text = text + tmptext
    if FORMAT != "markmap":
        text = text + "# Phases :  \n"
    text = add_file_in_readme(text,content,dpath)
    if FORMAT != "markmap":
        text = text + "# Listes des fichiers associés\n"
        for f in file_list:
            text = text + "- ["+f+"]"+"(./"+f+"), \n"
    summaryFilename = ""
    if FORMAT == "md":
        summaryFilename = "Readme.md"
    elif FORMAT == "markmap":
        summaryFilename = "index.html"
    else:
        if dpath[-1]=="/":
            summaryFilename = dpath.split("/")[-2] + ".md"
        else:
            summaryFilename = dpath.split("/")[-1] + ".md"
    with open(dpath+summaryFilename,'w') as wfile:
        wfile.write(text)
    return directories
    
def generate_doc(src, dest):
    # print("src : "+src)
    dir = []
    if FORMAT == "markmap":
        dir = generate_markmap_readme(src, dest)
    else :
        dir = generate_readme(src, dest)
    for directory in dir:
        #generate_readme(src+"/"+directory,dest+"/"+directory)
        generate_doc(src+"/"+directory,dest+"/"+directory)

# Define argparse
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", "-v", help="Augmente le niveau de verbosité",
                    action="store_true")
parser.add_argument("--format", "-f", help="Format de sortie optimisée pour : web, obsidian et markmap", choices=["web","md","obsidian","markmap"], default="web", required=False)
parser.add_argument("--name", "-n", help="Nom du projet, par défaut redview",  default="redview", required=False)
parser.add_argument("--path", "-p", help="Chemin destination de des notes formatées, par défaut /tmp/",  default="/tmp/", required=False)
parser.add_argument("--source", "-s", help="Source directory wich contains original md files")
args = parser.parse_args()

FORMAT = args.format

dest_path = args.path
dest_dir = args.name
dest = dest_path + dest_dir + "/"

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

if FORMAT == "web":
    FORMAT = "markmap"
    generate_doc(src,dest)
    FORMAT = "md"
generate_doc(src,dest)
# if FORMAT == "markmap":
#     FORMAT =  "web"
#     generate_doc(src, dest)
