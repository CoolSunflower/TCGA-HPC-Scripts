# Script gen for TCGA Tasks

## Directory structure
```
Assume the following directory structure:
Folder on HPC Server with your username: abcd
abcd:
    |
    |-- {RootFolder} (Change Variable Below)
        |-- main.py and other code files
        |-- all .sh files
        |-- Folder: o_e_files/
        |-- Folder: Results/


For execution, execute the commands in script.txt from the main (abcd) folder.
```

## Generate tasks
1. Change the top level variable declaration in gen_scripts.py
2. Run `python gen_scripts.py`