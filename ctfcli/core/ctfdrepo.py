import os
from pathlib import Path
from ctfcli.core.yamlstuff import Yaml
from ctfcli.core.category import Category

from ctfcli.core.challenge import Challenge
from ctfcli.core.deployment import Deployment

from ctfcli.core.repository import Repository
from ctfcli.core.masterlist import Masterlist
from ctfcli.core.apisession import APIHandler
from ctfcli.utils.lintchallenge import Linter
from ctfcli.utils.utils import _processfoldertotarfile
from ctfcli.utils.utils import getsubdirs,redprint,DEBUG
from ctfcli.utils.utils import errorlogger,yellowboldprint,debuggreen,logger
from ctfcli.utils.utils import debugblue,debuggreen,debugred,debugyellow

from ctfcli.utils.utils import validationdict
###############################################################################
#
###############################################################################
class SandboxyCTFdRepository():
    """
    Backend to CTF Repository
    """
    def __init__(self,
                repositoryfolder:Path ,
                masterlistlocation
                ):
        self.masterlistlocation = masterlistlocation
        self.repofolder = repositoryfolder
        self.allowedcategories = list
        try:
            debuggreen("[+] Instancing a SandboxyCTFdRepository()")
            super(SandboxyCTFdRepository, self).__init__()
        except Exception as e:
            errorlogger(f"[-] FAILED: Instancing a SandboxyCTFdLinkage(){e}")

    def _createrepo(self, allowedcategories)-> Repository:
        '''
        Performs all the actions necessary to create a repository
        From the Challenges Folder in the DATAROOT

        Creates the masterlist and Repository objects

        Returns:
        Masterlist, Repo (Tuple): Two new data objects

        '''
        debuggreen("[+] Starting Repository Scan")
        dictofcategories = {}
        #repocategoryfolders = os.listdir(os.path.abspath(self.repofolder))
        repocategoryfolders = getsubdirs(self.repofolder)
        #debuggreen(f"[+] Categories: {[f'{folder}\n' for folder in repocategoryfolders]}")
        # itterate over folders in challenge directory
        for category in repocategoryfolders:
            categorypath = Path(os.path.join(self.repofolder, category))
            # if its a repository category folder in aproved list
            if category.stem in allowedcategories:
                # process the challenges in that category
                newcategory = self._processcategory(categorypath)
                # this dict contains the entire repository now
                dictofcategories[newcategory.name] = newcategory
        # assign all categories to repository class
        # using protoclass + dict expansion
        newrepo = Repository(**dictofcategories)
        # return this class to the upper level scope
        return newrepo

    def _addmasterlist(self, masterlist:Masterlist):
        '''
        Adds a masterlist file to self
        '''
        setattr(self,'masterlist',masterlist)

    def _processcategory(self,categorypath:Path)-> Category:
        '''
        Itterates over a Category folder to add challenges to the database
        '''
        debuggreen(f"[+] Found Category folder {categorypath.name}")
        #create a new Category and assign name based on folder
        newcategory = Category(categorypath.name,categorypath)        
        #get subfolder names in category directory
        categoryfolder = getsubdirs(newcategory.location)
        # itterate over the individual challenges
        for challengefolder in categoryfolder:
            # each in its own folder, name not required
            challengefolderpath = Path(self.repofolder,categorypath.name, challengefolder)
            debuggreen(f"[+] Found folder {challengefolderpath.name}")
            debugyellow(f'[+] {challengefolderpath}')
            try:
                # begin scanning and if necessary, file parsing
                # to create new Challenge() or Deployment() class's from folder contents
                newchallenge = self._validatefolder(challengefolderpath,
                                                newcategory.name, 
                                                validationdict = validationdict)
                # load yaml and scan folder
                yamlcontents = self._processfoldercontents(challengefolderpath)#,category)
                # create CHallenge based off those
                self._createchallenge(yamlcontents=yamlcontents)

                #if self._validatefolder(validationdict, "deployment"):
                #    debuggreen("[+] Found Deployment Challenge")
                #    # load yaml and scan folder, passing category down
                #    yamlcontents = self._processfoldercontents(challengefolderpath)#,category)
                    # create deployment based off those
                #    self._createdeployment(yamlcontents=yamlcontents)

                #assign challenge to category
                newcategory._addchallenge(newchallenge)

            except Exception:
                errorlogger('[-] Error Creating Challenge!')
                continue
        return newcategory
    
    '''
    def _scanfolder(self,folderpath:Path, category:str, validationdict:dict) -> Challenge:
        """
        scans the folder to branch to either depoloyment or standard challenge

        File definitions required for the challenges are used here
        """
        try:
            # get directory listing of specified folder path
            challengedirlist = os.listdir(os.path.normpath(folderpath))
            #challengeitempath = lambda challengedata: Path(os.path.abspath(os.path.join(folderpath,challengedata)))
            # if the folder validates as a standard challenge
            validdata = self._validatefolder(challengedirlist, validationdict, "standard"):
            if validdata:
                debuggreen("[+] Found Standard Challenge")
            else:
                pass
        except Exception:
            errorlogger("[-] ERROR: Challenge Folder contents do not conform to specification!")
    '''
        
    def _validatefolder(self,folderpath:Path, category:str,keywurd:str):#, validationdict:dict) -> Challenge:
        """
        Compares the folder contents against a predefined list of items
        feed it a dict and keyword to select list to validate against
        """
        try:
            # get directory listing of specified folder path
            challengedirlist = os.listdir(os.path.normpath(folderpath))
            #challengeitempath = lambda challengedata: Path(os.path.abspath(os.path.join(folderpath,challengedata)))
            validationlist:list = validationdict.get(keywurd)
            #make a truthyness placeholder
            # false in the beginning, lack of information means "untrustworthy"
            valid = False
            # review items in directory
            for item in challengedirlist:
                # if its not in the provided list
                if item not in validationlist:
                    # throw a debug message and pass over the item, its probably 
                    # required for the challenge
                    debugyellow(f"[-] Found Extraneous item in challenge folder : {item} ")
                    pass
                # if its in the list
                elif item in validationlist:
                    # let the truthyness variable be set/remain as true
                    debuggreen(f"[+] Found Valid Item {item}")
                    valid = True
                    # remove the item from the validation list
                    validationlist.remove(item)
            # if there is anything left in the validation list, 
            # the files required for the challenge are not all there
            validationlistlength = len(validationlist)
            if validationlistlength > 0:
                valid = False
                errorlogger(f"[-] Missing {validationlistlength} required item/s, rejecting entry")
                #debugred(f"[-] Missing {validationlistlength}required item/s, rejecting entry")
                return valid
            elif validationlistlength == 0:
                debuggreen("[+] All Required files have been found in the specified folder")
                return valid
        except Exception:
            errorlogger("[-] ERROR: Challenge Folder contents do not conform to specification!")

        
    def _processfoldercontents(folderpath:Path,category:str)-> dict:
        """
        Performs linting of challenge spec file and compresses the solution/handout folders

        Arguments are the following:
            kwargs:dict     folder directory listing
                            {filename:str : Path}
            category:str    String containing the category folder name
        
        TODO: if category folder name does not match challenge category
            as given in yaml, reject or move to correct folder

        Returns the processed folder contents in the following format

        >>>    folderscanresults = {
        >>>        "category": category,
        >>>        "yaml":yamlcontents,
        >>>        "folderdata" : {
        >>>            "handout":handout, 
        >>>            "solution": solution
        >>>        }
        >>>    }

        """
        challengedirlist = os.listdir(os.path.normpath(folderpath))
        # get path to challenge subitem
        kwargs = {}
        #challenge contents definition for discerning between deployment 
        # and non deployment challenge
        try:
            # itterate over the items in the directory
            for item in challengedirlist:
            # get the paths
                itempath = Path(os.path.abspath(os.path.join(folderpath,item)))
                # assign paths to dict as {filename:path}
                kwargs[str(itempath.stem).lower()] =  itempath
            # pack up solution
            solution = _processfoldertotarfile(folder = kwargs.pop('handout'), 
                                               filename = 'solution.tar.gz')
            # pack up handout
            handout  = _processfoldertotarfile(folder = kwargs.pop('solution'), 
                                               filename = 'handout.tar.gz')
            # start the linter
            linter = Linter()
            # instance a Yaml class
            challengeyaml = Yaml().loadyaml(kwargs.pop("challenge"))
            # lint the challenge
            #shitty hack to get thins flowing properly
            # when everything is modified finally this can get removed
            #challengeyaml.update({"category": category})
            challengeyaml["category"] = category
            yamlcontents = linter.lintchallengeyaml(challengeyaml)
            folderscanresults = {
                "category": category,
                "yaml":yamlcontents,
                "folderdata" : {
                    "handout":handout, 
                    "solution": solution
                }
            }
            #debugblue(f"[DEBUG] VAR folderscanresults:dict \n[DEBUG] {folderscanresults}")
            return folderscanresults
        except Exception:
            errorlogger("[-] ERROR: _processfoldercontents() Encountered an Exception, Please check the log file")

    def _createdeployment(self, folderdata:dict, yamlcontents:dict) -> Challenge:
        """
        Creates a DeploymentChallenge() from a challenge folder containing a dockerfile 
        or a kubernetes spec
        """
        # create the challenge in the repository
        newdeployment = Deployment(
                category = folderdata.get("category"),
                handout=  folderdata.get("folderdata")["handout"],
                solution=  folderdata.get("folderdata")["solution"],
                readme = folderdata.get("folderdata")['README']
                )
            #load the challenge yaml dict into the class
        newdeployment._initchallenge(**folderdata.get("yaml"))
        return newdeployment

    def _createchallenge(self, folderdata:dict) -> Challenge:
        '''
        Create a njew Challenge() class based on the results of the folder scan
        if the folder scan was successful
        Args:
            folderscanresults (dict): representation of folder data
        '''
            # create the challenge in the repository
        newchallenge = Challenge(
                category = folderdata.get("category"),
                handout=  folderdata.get("folderdata")["handout"],
                solution=  folderdata.get("folderdata")["solution"],
                readme = folderdata.get("folderdata")['README']
                )
            #load the challenge yaml dict into the class
        newchallenge._initchallenge(**folderdata.get("yaml"))
        return newchallenge
        # generate challenge based on folder contents

    def _setcategory(self, repo:Repository, category:Category):
        """
        Adds a Category to the class
        We are adding classes to this class with "setattr"
        """
        setattr(repo, category.name, category)
        
    def _getcategory(self,repo:Repository, category:str)-> Category:
        """
        Returns The Category
        
        Args:
            repo (Repository) : Repository object created by masterlist
            category (str): the name of the category to return the challenges from
        
        Returns: 
        """
        # for each item in class
        for selfmember in dir(repo):
            # if its a Category, and not a hidden class attribute or function
            if (type(selfmember) == Category):#in CATEGORIES) and (selfmember.startswith("__") != True):
                return getattr(repo,selfmember)
                

    def listcategories(self):
        """
        Lists all categories
        """
        selflist = vars(self)
        categorylist = []
        for item in selflist:
            if type(item) == Category:
                categorylist.append(item)

    def removecategory(self, category:str):
        """
        Removes a category from the repository

        Args:

            category (str): Name of the category to unlink
        """

    def addcategory(self, category:Path):
        """
        Adds a Category to the repository

        Args:
            category (Path): path to category folder, in category level of repository
        """        
        #TODO: add entry to masterlist.yaml

    def synccategory(self):
        """
    Updates all challenges in CTFd with the versions in the repository
    Operates on the entire category 
        """
        #call 
    
    def _listchallenges(self):
        """
        Returns a list of all the installed challenges

        This is for local only, and is called by self.listchallenges()
        """

    def listchallenges(self, ctfdurl, ctfdtoken, remote=False):
        """
        NOT IMPLEMENTED YET

        Lists the challenges installed to the server
        Use 
        >>> --remote=False 
        to check the LOCAL repository
        For git operations, use `gitops` or your preferred terminal workflow

        Args:
            remote (bool): If True, Checks CTFd server for installed challenges
        """
        if remote == True:
            self.setauth(ctfdurl,ctfdtoken)#,adminusername,adminpassword)
            apicall = APIHandler( ctfdurl, ctfdtoken)
            challenges = apicall.get(apicall._getroute('challenges', admin=True), json=True).json()["data"]
            print(challenges)
        elif remote == False:
            #self.listsyncedchallenges()
            pass

    def removechallenge(self):
        """
        Removes a challenge from the repository
        Does not delete files, only unlinks
        """

    def syncchallenge(self):
        """
        
        """
    def updaterepository(self, challenge):
        """
    Updates the repository with any new content added to the category given
    if it doesnt fit the spec, it will issue an error    
    Try not to let your repo get cluttered
        """
