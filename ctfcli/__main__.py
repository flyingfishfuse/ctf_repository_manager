from configparser import ConfigParser
import configparser
import os,sys,fire
#from ctfcli.utils.config import Config
from pathlib import Path
from __main__ import PROJECT_ROOT

from ctfcli.utils.utils import DEBUG,is_named_directory
from ctfcli.utils.utils import errorlogger, yellowboldprint,greenprint,redprint
from ctfcli.utils.utils import debugblue,debuggreen,debugred,debugyellow

from ctfcli.utils.config import Config
from ctfcli.linkage import SandBoxyCTFdLinkage
from ctfcli.core.gitrepo import SandboxyGitRepository

################################################################################
##############                   Master Values                 #################
################################################################################

sys.path.insert(0, os.path.abspath('.'))

#Before we load the menu, we need to do some checks
# The .env needs to be reloaded in the case of other alterations
#
# Where the terminal is located when you run the file

debuggreen(" getting pwd of terminal")
global PWD
PWD = os.path.realpath(".")
#PWD_LIST = os.listdir(PWD)


# the tool should be sitting alongside the data folder where
# the challenges are located as a subfolder
global TOOL_LOCATION
debuggreen("getting path to tool directory")
TOOL_LOCATION = os.path.realpath(__file__)
debugyellow(TOOL_LOCATION)

###############################################################################

class SetPaths():
    def __init__(self,config_object:configparser.ConfigParser):
        '''sets various important locations'''
        self.PROJECT_ROOT:Path
        self.MASTERLIST_PATH:Path
        self.CONFIG_PATH:Path
        self.config = config_object

    def project_root(self, path_to_folder:Path) -> str:
        '''assign specified folder as project root
        This folder should have a folder named "challenges" that fits the spec
        outlined in the README.MD
        '''
        debuggreen("getting path to expected project directory, this should be the parent \
                    of the tool folder although you can assign your own \n  \
                    This can be changed using 'set_root project_root <full path to folder>'")
        # linter throwing an error on this one?
        self.PROJECT_ROOT = Path(os.path.realpath(path_to_folder))
        debugyellow(self.PROJECT_ROOT)
        self.config.set(section="Default",option='projectroot',value=str(self.PROJECT_ROOT))
        self._writeconfig()
        return str(self.PROJECT_ROOT)

    def set_masterlist(self, masterlist_location:Path) -> str:
        '''assign specified master list to configuration'''
        debuggreen("getting path to masterlist location,")
        self.MASTERLIST_PATH = Path(os.path.realpath(masterlist_location))
        debugyellow(self.MASTERLIST_PATH)
        self.config.set(section="Default",option='masterlistlocation',value=str(self.MASTERLIST_PATH))
        return str(self.MASTERLIST_PATH)

    def set_challenge_repository_dir(self, repository_dir:Path) -> str:
        ''' set location of challenges folder'''
        # The CTFd data should be constrained to a data folder for cleanliness
        debuggreen("getting expected path to ctfd data folder ")
        self.CHALLENGEREPOROOT=os.path.realpath(repository_dir)
        debugyellow(self.CHALLENGEREPOROOT)
        return str(self.CHALLENGEREPOROOT)
    
    def _set_config_location(self, config_location:Path) -> str:
        '''in the future the user will be able to specify multiple locations
        for multiple deployments with the same UI'''
        debuggreen("getting path to config location,")
        if config_location == '':
            self.CONFIG_PATH = Path(PROJECT_ROOT, 'config.cfg')
            #self.CONFIG_PATH = os.path.realpath(config_location)
        else:
            self.CONFIG_PATH = config_location
        debugyellow(self.CONFIG_PATH)
        return str(self.CONFIG_PATH)

    def _writeconfig(self):
        ''' writes locations to config'''
        with open(self.CONFIG_PATH, 'w') as configfile:
            self.config.write(configfile)

class Ctfcli():
    '''
        Proper Usage is as follows

        folder: ctfcli
        folder: data
            folder: CTFd
                folder: challenges
                    folder: category A
                    folder: category B
                    folder: ... so on and so on
                file:   masterlist.yaml
        
        FIRST RUN, If you have not modified the repository this is not necessary!
        This will generate a Masterlist.yaml file that contains the contents of the 
        repository for loading into the program
        >>> host@server$> python ./ctfcli/ ctfdrepo init

        you should provide token and url when running the tool, it will store 
        token only for a limited time. This is intentional and will not be changed
        This tool is capable of getting its own tokens given an administrative username
        and password

        for SINGLE operations, with NO authentication persistance:
        Replace <URL> with your CTFd website url
        Replace <TOKEN> with your CTFd website token
        >>> host@server$> python ./ctfcli/ ctfcli --ctfdurl <URL> --ctfdtoken <TOKEN>

        for multiple operations, WITH authentication persistance:
        This configuration will be able to obtain tokens via CLI
        >>> host@server$> python ./ctfcli/ ctfcli --ctfdurl <URL> --adminusername moop --adminpassword password

        To sync repository contents to CTFd Server, 
        >>> host@server$> python ./ctfcli/ ctfcli syncrepository 

        Not supplying a password/username, or token, will attempt to read auth
        information already in the config./cfg file

        You can obtain a auth token from the "settings" page in the "admin panel"
        This will initialize the repository, from there, you can either:
        
        Pull a remote repository
        you have to create a new masterlist after this
        That will be covered further down.
        >>> host@server$> ctfd.py gitops createremoterepo https://REMOTE_REPO_URL.git

        Generating a completion script and adding it to ~/.bashrc
        >>> host@server$>python ./ctfcli/ ctfcli -- --completion > ~/.ctfcli-completion
        >>> host@server$> echo "source ~/.ctfcli-completion" >> ~/.bashrc  

        To generate a completion script for the Fish shell. 
        (fish is nice but incompatible with bash scripts so far as I know so start.sh wont work)
        >>> -- --completion fish 

        If the commands available in the Fire CLI change, you'll have to regenerate the 
        completion script and source it again.

        / NOT IMPLEMENTED YET /
        IF YOU ARE MOVING YOUR INSTALLATION AFTER USING THE PACKER/UNPACKER
        IN START.SH, PERFORM THE FOLLOWING ACTIONS/COMMANDS
        >>> host@server$>python ./ctfcli/ ctfcli check_install
        / NOT IMPLEMENTED YET /

        control flow:
            set environment
            grab config and internalize
            instantiate linkage between tool and functionality
                masterlist not required

    '''
    def __init__(self):
        '''
        DO NOT make the software do any data operations in the __init__ 
        this is a CLI program that is controlled by the user and
        ALL operations that are anything beyond getting as framework 
        setup are verboten!
        '''
        # process config file
        # bring in config functions
        try:
            debuggreen("setting location of tool folder")
            self._toolfolder = Path(os.path.dirname(__file__)).parent.resolve()
            greenprint(f"[+] ctfcli tool folder Located at {self._toolfolder}")
            self.config = Config(Path(self._toolfolder, "config.cfg"))
        except Exception:
            errorlogger("Could not find tool folder and set config, check permissions and file existance")

        # this can be reassigned for allowing the challenges to sit alongside the tool
        # in a future revision it may be required
        #PROJECT_ROOT = Path(os.path.join(os.path.dirname(__file__), '..'))
        important_paths          = SetPaths(self.config.config)
        self.PROJECT_ROOT        = important_paths.project_root(Path(TOOL_LOCATION).parent)
        #self.CONFIG_LOCATION     = important_paths._set_config_location(str(Path(important_paths.PROJECT_ROOT, "config.cfg")))
        self.MASTERLIST_LOCATION = important_paths.set_masterlist(Path(important_paths.PROJECT_ROOT, "masterlist.yaml"))
        self.CHALLENGEREPOROOT   = important_paths.set_challenge_repository_dir(Path(PROJECT_ROOT,'/data/CTFd/challenges'))

        # this step checks for the challenges folder and other required things
        # will throw exception and EXIT if requirements are not met
        self._setenv()
        # create empty Repository() Object
        # requires location of challenges folder
        self.ctfdrepo = SandBoxyCTFdLinkage(repositoryfolder   = Path(self.CHALLENGEREPOROOT), 
                                            masterlistlocation = Path(self.MASTERLIST_LOCATION))
        # load config file
        self.ctfdrepo._initconfig(self.config)
        # challenge templates, change this to use your own with a randomizer
        #self.TEMPLATESDIR = Path(self.toolfolder , "ctfcli", "templates")


        self._validate_locations()

        #self._set_locations()
        self._challengesfolder = Path(self._reporoot, "challenges")
        #self.masterlist = Path(self._reporoot, "masterlist.yaml")
        self.configfile = Path(PROJECT_ROOT, "config.cfg")

        yellowboldprint(f'[+] Repository root ENV variable is {os.getenv("REPOROOT")}')
        yellowboldprint(f'[+] Challenge root is {self._challengesfolder}')
        # this code is inactive currently

        # create git repository
        try:
            # we do this last so we can add all the created files to the git repo        
            # this is the git backend, operate this seperately
            self.gitops = SandboxyGitRepository(Path(self.PROJECT_ROOT))
            #self.gitops.createprojectrepo()
        except Exception:
            errorlogger("[-] Git Repository Creation Failed, check the logfile")
        
    #def set_config_location(self, config_location:str):
    #    debuggreen("getting path to config location,")
    #    self.CONFIG_PATH = os.path.realpath(config_location)
    #    debugyellow(self.CONFIG_PATH)

    def _setenv(self):
        """
        Handles environment switching from being a 
        standlone module to being a submodule
        """
        # Set this parent folder as project root
        # ctfcli tool is in a subfolder and we are calling it from the main repository
        # we need it as an env var and local var
        os.environ["PROJECT_ROOT"] = str(self.PROJECT_ROOT) #str(self._toolfolder.parent)
        os.environ["MASTERLIST_LOCATION"] = str(self.MASTERLIST_LOCATION)
        #os.environ["CONFIG_LOCATION"] = str(self.CONFIG_LOCATION)
    
    def _get_project_root(self,path_to_folder:Path):
        ''' sets a variable with the location of the root folder for the project'''
        debuggreen("getting path to expected project directory, this should be the parent \
                    of the tool folder although you can assign your own \n  \
                    This can be changed using 'ctfcli change project path'")
        self.PROJECT_ROOT = Path(os.path.dirname(path_to_folder))
        debugyellow(self.PROJECT_ROOT)

    def _get_challenge_folder(self):
        '''sets a variable with the location of the challenge folder'''

    def _get_masterlist(self):
        '''sets a variable with the location of the masterlist.yaml'''


    def _validate_locations(self):
        ''' Validation for folder and data locations to ensure smooth operation '''

        #if __name__ == "__main__":
            # TODO: make function to check if they put it next to
            #  an actual repository fitting the spec
        try:
            if Path(self.CHALLENGEREPOROOT).is_dir():
                yellowboldprint("[+] Challenge Folder Found, presuming to be repository location")
                # the repository is the directory above this, containing all the things
            else:
                yellowboldprint("[!] Challenge folder not found!")
        except Exception:
            errorlogger("[-] Error, cannot find repository! ")


    def _set_locations():
        '''
        validates the locations of important items
        Sets variables with the locations of the following items:
        masterlist.yaml
        challenges directory
        config folder
        '''
        debuggreen("Setting locations of all important items")
        #################################################################
        # Setting location of challenges folder
        #################################################################
        # set var to indicate folder hierarchy
        onelevelup = self._toolfolder.parent
        debugyellow(f" one folder up : {onelevelup}")
        # if a folder named challenges is in the directory next to this one
        greenprint("[+] Looking for challenges folder")
        try:
            for item in os.listdir(onelevelup):
                debugyellow(f"itterating - directory listing item: {item}")
                if os.path.isdir(item) and item == "challenges":
                    yellowboldprint("[+] Challenge Folder Found alongside tool folder, presuming to be repository location")
                    # set var to challenge folder location
                    self._challengesfolder = os.path.join(onelevelup, "challenges")
                    # set var to repository root
                    self._reporoot = onelevelup
                    debuggreen(f"challenges folder at {self._challengesfolder}")
                    debuggreen(f"repository root folder at {self._reporoot}")
                    break
                # not the droid/folder we are looking for
                elif (os.path.isdir(item) and item != "challenges"):
                    debugyellow(f"folder is not repository folder named 'challenges' : {item}")
                    continue
                # not even a droid/folder
                elif not os.path.isdir(item):
                    debugyellow(f"item is not folder or named challenges : {item}")
                    continue
                # folder one level up is empty?
                else:
                    yellowboldprint("[!] Challenge folder not found Alongside tool folder, Exiting program!")
                    raise Exception
        except Exception:
            errorlogger("[-] Error, cannot find repository! ")
    #################################################################
    # Setting location of masterlist
    #################################################################
        try:
            # location of the all important masterlist
            # # ~/meeplabben/data/masterlist.yaml
            self.masterlist = Path(self._reporoot, "masterlist.yaml")
            yellowboldprint(f'[+] Masterlist is expected to be at {self.masterlist}')
        except Exception:
            errorlogger("[-] failed to set masterlist location")
    #################################################################
    # Setting location of config file
    #################################################################
        try:    
            # location of the config file
            # ~/meeplabben/config.cfg
            self.configfile = Path(self._reporoot, "config.cfg")
            yellowboldprint(f'[+] Config File is expected to be at {self.configfile}')

            # bring in config functions
            self.config = Config(self.configfile)
            self.set_config()
        except Exception:
            errorlogger("[-] Failed to set location of config file")

    def _getenv(self):
        '''
        FUTURE
        Retrieves neceessary env vars if running in submodule mode
        all variables should be a Path to a location nearby
        '''
        debugyellow("Loading the following variables from the shell environment")
        for var_name in self.important_env_list:
            debugblue(var_name)
        for each in self.important_env_list:
            debugyellow("setting  env")
            debugyellow(f"SETTING {each} as {os.getenv(each)}")
            setattr(self,each, Path(os.getenv(each)))
 
def main():
   '''wat'''
    commands = {
        "ctfcli"     : Ctfcli,
        "set_root"   : Setroot
        #"load_config": LoadConfig
        }
   #fire.Fire(Ctfcli)
   fire.Fire(commands)

if __name__ == "__main__":
    main()
    #fire.Fire(Ctfcli)