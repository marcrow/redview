# redview
View markdown file tree in a fancy web interface. Two display mode github like and markmap to have an overview of your files.

## Features
- Create summary at the top of each md file.
- Create md summary file in each directory to link md files together.
- Node JS web server to preview md like in github or you can also add your own style.
- Search feature on the web server to find specific content in md note.
- Node JS web server to preview md as a mindmap with markmap.
- No internet connexion required

## When use Redview
1. Preview knowledge notes
  - Stay compatible with all markdown based tools used to take note (gitbook, github...)
  - Take your note from everywhere, on the web, in vs code, in a notepad or in vi.
  - Preview your notes offline
  - See your notes as mind map without modification to have a global view. In case of pentest notes, it can be used as a "to be done" view to quickly know what tests have to be done on a specific target.
  - Search quickly data in your notes
3. Work on large pentest/audit results
  - Preview a large amount of data with mindmap
  - Search for specific keyword
4. View massive md file tree
  - same argument as for note preview knowledge preview.
    
## How it works
When you run the python script a copy of the project is created in the directory provide in argument (/tmp/redview by default). In this new directory, summary are added at the top of each files and directory summary are created for each directory. In addition html file are created for markmap preview.

## How it will works (in the future)
In addition of the current usage, redview will be able to work on the same directory of the original directory.   
Update from source file will be done automatically.  
Search based on tags set in yaml at the the top of md files.  
Update your sql from your md note and vice versa.
