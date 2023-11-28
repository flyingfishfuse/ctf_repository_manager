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

class Setpaths():
    def __init__(self,config_object:configparser.ConfigParser):
        '''sets various important locations'''
        #self.PROJECT_ROOT = Path
        #self.MASTERLIST_PATH = Path
        #self.CONFIG_PATH = Path
        self.config= config_object

    def project_root(self, path_to_folder:Path) -> Path:
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
        return self.PROJECT_ROOT

    def set_masterlist(self, masterlist_location:Path) -> Path:
        '''assign specified master list to configuration'''
        debuggreen("getting path to masterlist location,")
        self.MASTERLIST_PATH = Path(os.path.realpath(masterlist_location))
        debugyellow(self.MASTERLIST_PATH)
        self.config.set(section="Default",option='masterlistlocation',value=str(self.MASTERLIST_PATH))
        return self.MASTERLIST_PATH

    def set_challenge_repository_dir(self, repository_dir:Path) -> Path:
        ''' set location of challenges folder'''
        # The CTFd data should be constrained to a data folder for cleanliness
        debuggreen("getting expected path to ctfd data folder ")
        #self.CHALLENGEREPOROOT=os.path.realpath(repository_dir)
        self.CHALLENGEREPOROOT=Path(repository_dir, "").resolve()
        debugyellow(self.CHALLENGEREPOROOT)
        return self.CHALLENGEREPOROOT
    
    def _set_config_location(self, config_location:Path) -> Path:
        '''in the future the user will be able to specify multiple locations
        for multiple deployments with the same UI'''
        debuggreen("getting path to config location,")
        if config_location == '':
            self.CONFIG_PATH = Path(PROJECT_ROOT, 'config.cfg')
            #self.CONFIG_PATH = os.path.realpath(config_location)
        else:
            self.CONFIG_PATH = config_location
        debugyellow(self.CONFIG_PATH)
        return self.CONFIG_PATH

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
    def __init__(self, config_location:str="./config.cfg"):
        '''
        DO NOT make the software do any data operations in the __init__ 
        this is a CLI program that is controlled by the user and
        ALL operations that are anything beyond getting as framework 
        setup are verboten!
        '''
        # step 1: Get config
            # default
            #   or
            # user supplied
        try:
            # set paths relative to the location of this folder
            debuggreen("setting location of tool folder")
            self._toolfolder = Path(os.path.dirname(__file__)).parent.resolve()
            greenprint(f"[+] ctfcli tool folder Located at {self._toolfolder}")
            # if config param is not modified by user it looks for config 
            # in parent folder of tool folder, otherwise it looks for
            # the config in the specified location
            try:
                self._config_set_check(config_location)
                #self.config = Config(Path(self._toolfolder, "config.cfg"))
                self.config = Config(self.CONFIG_LOCATION)
            except Exception:
                errorlogger("Could not set config location: check if file exists and permissions")
        except Exception:
            errorlogger("Could not find tool folder and set config, check permissions and file existance")

        # step 2: set paths
        important_paths          = Setpaths(self.config.config)
        self.CONFIG_LOCATION     = important_paths._set_config_location(Path(important_paths.PROJECT_ROOT, "config.cfg"))
        self.PROJECT_ROOT        = important_paths.project_root(Path(TOOL_LOCATION).parent))
        self.MASTERLIST_LOCATION = important_paths.set_masterlist(Path(important_paths.PROJECT_ROOT, "masterlist.yaml"))
        self.CHALLENGEREPOROOT   = important_paths.set_challenge_repository_dir(Path(PROJECT_ROOT,'/data/CTFd/challenges'))

        #self._setenv()

        # currently, only the challenge folder needs validation
        self._validate_locations()

    def init(self):
        ''' '''
        # create empty Repository() Object
        # requires location of challenges folder
        important_items={'repository' : self.CHALLENGEREPOROOT, 
                'masterlist' : self.MASTERLIST_LOCATION
                }
        repo = SandBoxyCTFdLinkage(important_items)
        # load config file
        repo._initconfig(self.config)
        # challenge templates, change this to use your own with a randomizer
        #self.TEMPLATESDIR = Path(self.toolfolder , "ctfcli", "templates")

    def set():
        '''Sets variables for operation'''

    def _config_set_check(self,config_location:str):
        '''Checks if user gave custom config location and sets new values accordingly
        The results of this are stored in the Masterlist.yaml'''
        #if config param not used on CLI
        if config_location == "./config.cfg":
            greenprint("Using default configuration file")
            self.CONFIG_LOCATION = Path(TOOL_LOCATION).parent / config_location
        
        else:
            # get full path of location given if relative path supplied as argument
            self.CONFIG_LOCATION = Path(config_location).resolve()
    
    def _check_masterlist(self):
        '''Checks if master list is available'''


    def start_git(self):
        '''create git repository from $PROJECT_ROOT'''
        try:
            if os.getenv('PROJECT_ROOT') is not None:
                self.gitops = SandboxyGitRepository(Path(str(os.getenv('PROJECT_ROOT'))))
            # we do this last so we can add all the created files to the git repo        
            # this is the git backend, operate this seperately
            else:
                self.gitops = SandboxyGitRepository(Path(self.PROJECT_ROOT))
            #self.gitops.createprojectrepo()
        except Exception:
            errorlogger("[-] Git Repository Creation Failed, check the logfile")
        
    #def set_config_location(self, config_location:str):
    #    debuggreen("getting path to config location,")
    #    self.CONFIG_PATH = os.path.realpath(config_location)
    #    debugyellow(self.CONFIG_PATH)

    #def _setenv(self):
        """
        Handles environment switching from being a 
        standlone module to being a submodule
        """
        # Set this parent folder as project root
        # ctfcli tool is in a subfolder and we are calling it from the main repository
        # we need it as an env var and local var
    #    os.environ["PROJECT_ROOT"] = str(self.PROJECT_ROOT) #str(self._toolfolder.parent)
    #    os.environ["MASTERLIST_LOCATION"] = str(self.MASTERLIST_LOCATION)
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
            # challenge folder
            if Path(self.CHALLENGEREPOROOT).is_dir() and self.CHALLENGEREPOROOT.stem == "challenge":
                yellowboldprint("[+] Challenge Folder Found, presuming to be repository location")
                # the repository is the directory above this, containing all the things
            else:
                yellowboldprint("[!] Challenge folder not found!")
                raise Exception
        except Exception:
            errorlogger("[-] Error, cannot find repository! ")

    #def _getenv(self):
        '''
        FUTURE
        Retrieves neceessary env vars if running in submodule mode
        all variables should be a Path to a location nearby
        '''
    #    debugyellow("Loading the following variables from the shell environment")
    #    for var_name in self.important_env_list:
    #        debugblue(var_name)
    #    for each in self.important_env_list:
    #        debugyellow("setting  env")
    #        debugyellow(f"SETTING {each} as {os.getenv(each)}")
    #        setattr(self,each, Path(os.getenv(each)))
 
def main():
    '''wat'''
    #fire.Fire(Ctfcli)
    fire.Fire(Ctfcli)

if __name__ == "__main__":
    main()
    #fire.Fire(Ctfcli)