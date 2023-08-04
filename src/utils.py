import yaml

def replace_fr_char(text):
    replacements = {
        'é' : '233',
        'à' : '224',
        'è' : '232'
    }
    for old, new in replacements.items():
        text = text.replace(old,new)
        
    return text

def is_valid_integer(string_value):
    try:
        integer_value = int(string_value)
        return True
    except ValueError:
        return False

def add_phase_in_content(phases, files_content, cfile, content):
    for tag, titles in phases.items():
        tag = tag
        if tag == "":
            continue
        if not is_valid_integer(tag):
            print("Warning :"+cfile + " have an invalid tag ->"+tag)
            continue
        
        for title in titles:
            title1 = {}
            for index,  tmp_title in enumerate(files_content): #retrieve level1 title  
                if list(tmp_title.keys())[0].strip() == title.strip():
                    title1 = files_content[index]
                    continue
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

def getDirToExclude(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        main_structure = data['exclude']['directories']
        return main_structure
    return None 

def getFileToExclude(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        main_structure = data['exclude']['files']
        return main_structure
    return None 


