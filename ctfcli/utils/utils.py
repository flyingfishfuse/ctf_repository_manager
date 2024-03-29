import sys
import yaml
import os
import pathlib
import logging
import traceback
import tarfile
from pathlib import Path
global DEBUG
DEBUG = True

try:
    #import colorama
    from colorama import init
    init()
    from colorama import Fore, Back, Style
    COLORMEQUALIFIED = True
except ImportError as derp:
    print("[-] NO COLOR PRINTING FUNCTIONS AVAILABLE, Install the Colorama Package from pip")
    COLORMEQUALIFIED = False

################################################################################
##############               LOGGING AND ERRORS                #################
################################################################################

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('foo').debug('bah')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger('foo').debug('bah')

log_file            = 'logfile'
logging.basicConfig(filename=log_file, filemode='w')
                    #format='%(asctime)s %(message)s', 
if DEBUG == True:
    logger = logging.getLogger().setLevel(logging.DEBUG)
else:
    logger = logging.getLogger().setLevel(logging.INFO)

#logger.setLevel(logging.INFO)

launchercwd         = pathlib.Path().absolute()

redprint          = lambda text: print(Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
blueprint         = lambda text: print(Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
greenprint        = lambda text: print(Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
yellowboldprint   = lambda text: print(Fore.YELLOW + Style.BRIGHT + ' {} '.format(text) + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
makeyellow        = lambda text: Fore.YELLOW + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makered           = lambda text: Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makegreen         = lambda text: Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makeblue          = lambda text: Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
debugred          = lambda text: print(Fore.RED + '[DEBUG] ' +  str(text) + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debugblue         = lambda text: print(Fore.BLUE + '[DEBUG] ' +  str(text) + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debuggreen        = lambda text: print(Fore.GREEN + '[DEBUG] ' +  str(text) + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debugyellow       = lambda text: print(Fore.YELLOW + '[DEBUG] ' +  str(text) + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debuglog          = lambda message: logger.debug(message) 
infolog           = lambda message: logger.info(message)   
warninglog        = lambda message: logger.warning(message) 
errorlog          = lambda message: logger.error(message) 
criticallog       = lambda message: logger.critical(message)



# old code from ctfdrepo.py
#regularchallengelist = ["handout","solution","challenge", "README"] #.yaml","challenge.yml"]
#deploymentfoldercontents = ["deployment","Dockerfile","metadata.yaml","README"]

                # itterate over the items in the directory
                #for item in challengedirlist:
                    # get the paths
                    #itempath = challengeitempath(item)
                    # assign paths to dict as {filename:path}
                    #kwargs[str(itempath.stem).lower()] =  itempath

            # for list of all item in dir
            #for item in challengedirlist:
            #    itempath = challengeitempath(item)
                # if the item is in the list of approved items
                # for a regular non-deployment challenge
                #for validationitemslist in validationdict:
                #    self._validatefolder(validationdict, )
                #if itempath.stem in regularchallengelist:
                #    debuggreen(f"[+] Found : {item}")
            #    kwargs[str(itempath.stem).lower()] =  itempath
                # if its a readme
                #elif itempath.stem == "README":
                #    kwargs[str(itempath.stem).lower()] = itempath
                # extra stuff not in approved list of contents
                #elif itempath.stem not in regularchallengelist:
                    # ignore it
                #    continue
                # all other conditions
                #else:
                    #logger.error(f"[-] missing important item in challenge folder, skipping : missing {item}")
                #    break

#this is where everything is defined, the structure of the repo folders
validationdict = {
            "standard":["handout","solution","challenge.yaml", "README"],
            # if these exist, make a deployment instead
            "deployment": ["deployment","Dockerfile","metadata.yaml","README"]
    }
###############################################
# returns subdirectories , without . files/dirs
# name of the yaml file expected to have the challenge data in each subfolder
basechallengeyaml   = "challenge.yml"
def getsubdirs(directory):
    '''
    Returns folders in a directory as Paths
    '''
    wat = []
    for filepath in pathlib.Path(directory).iterdir():
       if (Path(filepath).is_dir()):
           wat.append(Path(filepath))
    return wat

def getsubfiles(directory):
    '''
    Returns files in a directory as Paths
    '''
    wat = [Path(filepath) for filepath in pathlib.Path(directory).glob('**/*')]
    return wat

# open with read operation
challengeyamlbufferr = lambda category,challenge: open(os.path.join(category,challenge,basechallengeyaml),'r')
# open with write operation
challengeyamlbufferw = lambda category,challenge: open(os.path.join(category,challenge,basechallengeyaml),'r')
#loads a challenge.yaml file into a buffer
loadchallengeyaml =  lambda category,challenge: yaml.load(challengeyamlbufferr(category,challenge), Loader=yaml.FullLoader)
writechallengeyaml =  lambda category,challenge: yaml.load(challengeyamlbufferw(category,challenge), Loader=yaml.FullLoader)
# simulation of a chdir command to "walk" through the repo
# helps metally
#location = lambda currentdirectory,childorsibling: Path(currentdirectory,childorsibling)
# gets path of a file
getpath = lambda directoryitem: Path(os.path.abspath(directoryitem))

################################################################################
##############             ERROR HANDLING FUNCTIONS            #################
################################################################################
def errorlogger(message):
    """
    prints line number and traceback
    TODO: save stack trace to error log
            only print linenumber and function failure
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    trace = traceback.TracebackException(exc_type, exc_value, exc_tb) 
    lineno = 'LINE NUMBER : ' + str(exc_tb.tb_lineno)
    logger.error(
        redprint(
            message+"\n [-] "+lineno+"\n [-] "+''.join(trace.format_exception_only()) +"\n"
            )
        )

def get_directory(path:Path, directory_name:str) -> Path | bool:
    ''' Check if something is a directory with a specific name
    Args:
        path (path): full or relative path to directory expected to contain item
        directory_name (str): the name of the directory whos existance you wish to determine
    Returns:
        Path : Path of the directory, if it exists
        bool: False is not there

    '''
    try:
        # I got this from Bing AI so there might be issues with it
        item_of_interest = (lambda x: x[0] if x else exec('assert False, "List is empty"'))([item for item in path.iterdir() if item.is_dir() and item.stem == directory_name])
        return item_of_interest
    except ValueError:
        errorlogger("Directory not in location specified: %s" % path)
        return False

def check_file_exist(path:Path, item_name:str, item_extension_type:str) -> Path | bool:
    ''' Check if specified file exists
    Args:
        path (path): full or relative path to directory expected to contain item
        item_name (str): the name of the item whos existance you wish to determine
        item_extension_type (str): The file extension of the item you wish to determine the existence of
    Returns:
        Path : Path of the item, if it exists
        bool: False is not there

    '''
    try:
        # I got this from Bing AI so there might be issues with it
        item_of_interest = (lambda x: x[0] if x else False)([Path(item) for item in path.iterdir() if item.stem == item_name and item.suffix == item_extension_type])
        if item_of_interest == True:
            return item_of_interest
        else:
            return False
    except Exception:
        errorlogger("Masterlist not in expected location, if you did not move it, check permissions: %s" % path)
        return False

def _processfoldertotarfile(folder:Path,filename='default')-> tarfile.TarFile:
    '''
    creates a tarfile of the provided folder 
    if a tarfile already exists, it simply returns that
    '''
    try:
        dirlisting = [item for item in Path(folder).glob('**/*')]
        #for each in dirlisting:
        #    if each.stem == ".gitignore":
        # folder is not empty
        if len(dirlisting) != 0:
                # first, scan for the file.tar.gz
                for item in dirlisting:
                    # if its a hidden file
                    if item.stem.startswith("."):# == ".gitignore":
                        continue
                    # if its a file without an extension
                    if len(item.suffixes) == 0 and item.is_file():
                        continue
                    # a directory
                    if item.is_dir():
                        continue
                    # if its named filename.tar.gz
                    elif item.suffixes[0] == '.tar' and item.suffixes[1] == '.gz' and item.stem == filename:
                        #return TarFile.open(item,"r:gz",item)
                        return item
                    #else:
                    #    continue
                # if its not there, create archive and add all files
                newtarfilepath = Path(folder,filename)
                with tarfile.open(newtarfilepath, "w:gz") as tar:
                    for item in dirlisting:
                        if item.is_dir():
                            tar.add(item)
                        else:
                            tar.addfile(tarfile.TarInfo(item.name), open(item))
                tar.close()
                return newtarfilepath
        elif len(dirlisting) == 0:
            #TODO: add manual tar upload to challenge by name
            yellowboldprint(f"[?] No files in {folder} Folder. This must be uploaded manually if its a mistake")
            # cheat code for exiting a function?
            return None
        else:
            redprint("[-] Something WIERD happened, throw a banana and try again!")
            raise Exception
    except Exception as e:
        errorlogger(f'[-] Could not process challenge: {e}')
