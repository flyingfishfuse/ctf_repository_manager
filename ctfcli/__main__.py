import os,sys,fire
sys.path.insert(0, os.path.abspath('.'))
#from ctfcli.utils.config import Config
from pathlib import Path

from ctfcli.utils.utils import DEBUG
from ctfcli.utils.utils import errorlogger, yellowboldprint,greenprint,redprint

from ctfcli.utils.config import Config
from ctfcli.linkage import SandBoxyCTFdLinkage
from ctfcli.core.gitrepo import SandboxyGitRepository

###############################################################################
class Ctfcli():
    '''
        Proper Usage is as follows

        THIS TOOL SHOULD BE ALONGSIDE the challenges repository folder
        
        folder
            subfolder_challenges
                masterlist.yaml
                subfolder_category
            subfolder_ctfcli
                __main__.py
        
        FIRST RUN, If you have not modified the repository this is not necessary!
        This will generate a Masterlist.yaml file that contains the contents of the 
        repository for loading into the program
        >>> host@server$> python ./ctfcli/ ctfcli ctfdrepo init

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
        # modify the structure of the program here by reassigning classes

		# FUTURE DEVELOPMENTS
        # we import theswe if running in submodule mode
		self.important_env_list = [
			"PROJECT_ROOT",
			"CHALLENGEREPOROOT",
 			"COMPOSEDIRECTORY",
 			"KUBECONFIGPATH",
		]

        # this step checks for the challenges folder and other required things
        # will throw exception and EXIT if requirements are not met
        self._setenv()
        # process config file
        # bring in config functions
        self.config = Config(self.configfile)
        # create empty Repository() Object
        # requires location of challenges folder
        self.ctfdrepo = SandBoxyCTFdLinkage(self._challengesfolder, 
                                            self.masterlist)
        # load config file
        self.ctfdrepo._initconfig(self.config)
        # challenge templates, change this to use your own with a randomizer
        self.TEMPLATESDIR = Path(self._toolfolder , "ctfcli", "templates")

        # create git repository
        try:
            # we do this last so we can add all the created files to the git repo        
            # this is the git backend, operate this seperately
            self.gitops = SandboxyGitRepository(self._reporoot)
            #self.gitops.createprojectrepo()
        except Exception:
            errorlogger("[-] Git Repository Creation Failed, check the logfile")

	def _getenv(self):
		'''
		Retrieves neceessary env vars if running in submodule mode
		all variables should be a Path to a location nearby
		'''
		if DEBUG == True:
			debugyellow("Loading the following variables from the shell environment")
		for var_name in self.important_env_list:
			if DEBUG == True:
				debugblue(var_name)
		for each in self.important_env_list:
			if DEBUG == True:
				debugyellow("setting  env")
				debugyellow(f"SETTING {each} as {os.getenv(each)}")
			setattr(self,each, Path(os.getenv(each)))

    def _setenv(self):
        """
        Handles environment switching from being a 
        standlone module to being a submodule
        """
        debuggreen(" getting pwd of tool")
        PWD = Path(os.path.realpath("."))
        # this must be alongside the challenges folder if being used by itself
            # Master values
            # alter these accordingly
        debuggreen("setting location of tool folder")
        self._toolfolder   = Path(os.path.dirname(__file__))
        greenprint(f"[+] Tool folder Located at {self._toolfolder}")
        
        #----OLD---
        # maybe dont need this?
        # might change the spec later
        #if DEBUG == True:
        # set project root to simulate ctfcli being one context higher
        #----OLD---
        
        # Set this parent folder as project root
        # ctfcli tool is in a subfolder and we are calling it from the main repository
        # top level folder
        # data directory holds the challenges
        # we need it as an env var and local var
        os.environ["PROJECT_ROOT"] = str(self._toolfolder.parent)
        # just checking it got set
        try:
            PROJECT_ROOT = os.getenv('PROJECT_ROOT')
            self.root = PROJECT_ROOT
        except Exception:
            errorlogger("Could not find project root env variable after setting it. Check permissions and shell environment")
        
        if __name__ == "__main__":
            # TODO: make function to check if they put it next to
            #  an actual repository fitting the spec
            try:
                # check if alongside challenges folder,
                # i.e. individual tool usage
                #debuggreen("finding parent directory")
                #onelevelup = self._toolfolder.parent
                #oneleveluplistdir = os.listdir(onelevelup)
                #debuggreen("looking for challenges folder")
                # found an item named "challenge"
                if ('challenges' in oneleveluplistdir):
                    #is it a directory?
                    if os.path.isdir(oneleveluplistdir.get('challenges')):
                        yellowboldprint("[+] Challenge Folder Found, presuming to be repository location")
                        debuggreen("setting challenge folder to main class")
                        self._challengesfolder = os.path.join(onelevelup, "challenges")
                    # the repository is the directory above this, containing all the things
                    self._reporoot = onelevelup
                # did not find folder
                else:
                    yellowboldprint("[!] Challenge folder not found!")

                    if PROJECT_ROOT != None:
                        yellowboldprint(f"[+] Project root env var set as {PROJECT_ROOT}")
                        self._reporoot = Path(PROJECT_ROOT,"data","CTFd")
                    else:
                        yellowboldprint(f"[+] Project root env var NOT SET")

            except Exception:
                errorlogger("[-] Error, cannot find repository! ")
        else:
            from __main__ import PROJECT_ROOT
            self._reporoot = Path(PROJECT_ROOT,"data","CTFd")

        os.environ["REPOROOT"] = str(self._reporoot)

        set_locations()
        self._challengesfolder = Path(self._reporoot, "challenges")
        #self.masterlist = Path(self._reporoot, "masterlist.yaml")
        self.configfile = Path(PROJECT_ROOT, "config.cfg")

        yellowboldprint(f'[+] Repository root ENV variable is {os.getenv("REPOROOT")}')
        yellowboldprint(f'[+] Challenge root is {self._challengesfolder}')
        # this code is inactive currently

    def set_locations():
        '''
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
					continue
				# not even a droid/folder
				elif not os.path.isdir(item):
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

def main():
   fire.Fire(Ctfcli)

if __name__ == "__main__":
    main()
    #fire.Fire(Ctfcli)