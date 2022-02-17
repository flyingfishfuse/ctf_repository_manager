import os, sys
import yaml, pathlib, logging, traceback
from pathlib import Path
from yaml import SafeDumper,MappingNode,Dumper,Loader
from yaml import safe_load,safe_dump,add_representer

from hashlib import sha1
import kubernetes

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

####################################################################
## useful oneliners
####################################################################
getpath = lambda directoryitem: Path(os.path.abspath(directoryitem))
################################################################################
##############               LOGGING AND ERRORS                #################
################################################################################
log_file            = 'logfile'
logging.basicConfig(filename=log_file, 
                    #format='%(asctime)s %(message)s', 
                    filemode='w'
                    )
logger              = logging.getLogger()
launchercwd         = pathlib.Path().absolute()

redprint          = lambda text: print(Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
blueprint         = lambda text: print(Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
greenprint        = lambda text: print(Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
yellowboldprint = lambda text: print(Fore.YELLOW + Style.BRIGHT + ' {} '.format(text) + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
makeyellow        = lambda text: Fore.YELLOW + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makered           = lambda text: Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makegreen         = lambda text: Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makeblue          = lambda text: Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
debugred = lambda text: print(Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debugblue = lambda text: print(Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debuggreen = lambda text: print(Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debugyellow = lambda text: print(Fore.YELLOW + ' ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debuglog     = lambda message: logger.debug(message) 
infolog      = lambda message: logger.info(message)   
warninglog   = lambda message: logger.warning(message) 
errorlog     = lambda message: logger.error(message) 
criticallog  = lambda message: logger.critical(message)

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
        #redprint(
            message+"\n [-] "+lineno+"\n [-] "+''.join(trace.format_exception_only()) +"\n"
        #    )
        )


class Yaml(yaml.YAMLObject): #filetype
    """
    Base class for challenges and the repo

    Anything thats a yaml file inherits from this
    Args:
        filepath (str): Full Filepath to Yaml File to load
    """
    def __init__(self, filepath:Path=None):
        if filepath == None:
            pass
        else:
            self.filename = os.path.basename(filepath)
            self.filepath = filepath
            self.directory = self.filepath.parent
            #if self.filename.endswith(".yaml"):
            #    greenprint("[!] File is .yaml! Presuming to be kubernetes config!")
            #    self.type = "kubernetes"
            #elif self.filename.endswith(".yml"):
            #    greenprint("[!] Challenge File presumed (.yml)")
            #    self.type = "challenge"

    def loadyaml(self, filepath:Path) -> dict:
        """
        Loads the yaml specified by the class variable Yaml.filepath
        """
        # I copied the code to prevent having to go back and rewrite I 
        # think like ONE thing, so this can be cleaned up some
        self.filename = os.path.basename(filepath)
        self.filepath = filepath
        self.directory = self.filepath.parent
        #if self.filename.endswith(".yaml"):
        #    greenprint("[!] File is .yaml! Presuming to be kubernetes config!")
        #    self.type = "kubernetes"
        #elif self.filename.endswith(".yml"):
        #    greenprint("[!] Challenge File presumed (.yml)")
        #    self.type = "challenge"
        try:
            with open(filepath, 'r') as stream:
                return yaml.safe_load(stream)
        except Exception:
            errorlogger("[-] ERROR: Could not load .yml file")
    
    def writeyaml(self):
        """
        Remember to assign data to the file with

        >>> thing = Yaml(filepath)
        >>> thing.data['key'] = value
        """
        try:
            #open the yml file pointed to by the load operation
            with open(self.filepath) as file:
                safe_dump(file)
        except Exception:
            errorlogger("[-] ERROR: Could not Write .yml file, check the logs!")

class KubernetesYaml(Yaml): #file
    """
    Represents a Kubernetes specification
    future
    """
    def __new__(cls,*args, **kwargs):
        cls.__name__ = 'deployment'
        cls.__qualname__= cls.__name__
        cls.tag = '!deployment'
        return super(cls).__new__(cls, *args, **kwargs)
    
    def __init__(self,**entries): 
        print("[+] Generating new repository")
        self.__dict__.update(entries)
    
    def __repr__(self):
        '''
        '''
        wat = []
        for key in self.__dict__:
            wat.append(str(key) + " : " + str(self.__dict__[key]))
        #return self_repr
        return wat

###############################################################################
#  wat, someone tech me how to make this construct arbitrary classes?
###############################################################################
class YAMLMultiObjectMetaclass(yaml.YAMLObjectMetaclass):
    """
    The metaclass for YAMLMultiObject.
    """
    def __init__(cls, name, bases, kwds):
        super(YAMLMultiObjectMetaclass, cls).__init__(name, bases, kwds)
        if 'yaml_tag' in kwds and kwds['yaml_tag'] is not None:
            cls.yaml_loader.add_multi_constructor(cls.yaml_tag, cls.from_yaml)
            cls.yaml_dumper.add_multi_representer(cls, cls.to_yaml)

class YAMLMultiObject(yaml.YAMLObject, metaclass=YAMLMultiObjectMetaclass):
    """
    An object that dumps itself to a stream.
    
    Use this class instead of YAMLObject in case 'to_yaml' and 'from_yaml' should
    be inherited by subclasses.
    """
    pass


class MyDumper(yaml.SafeDumper):
    def represent_data(self, data):
        if isinstance(data, Enum):
            return self.represent_data(data.value)
        return super().represent_data(data)

class Foo(Enum):
    A = 1
    B = 2

data = {
    'value1': Foo.A,
}

yaml.dump(data, Dumper=MyDumper)
class Constructor(yaml):
    """
    This is one way of turning a yaml file into python code

    https://matthewpburruss.com/post/yaml/

    """
    def __init__(self):
        #self.repotag = "!Repo:"
        #self.categorytag = "!Category:"
        #self.challengetag = "!Challenge:"
        self.nodetags = {
            "":"!Repo:",
            "":"!Category:",
            "":"!Challenge:",
            "":"!Deployment:",
            
        }
        self.represent = lambda tag,dumper,codeobject: dumper.represent_mapping(tag, codeobject.__dict__)
        super().__init__()

    def _representer(self, tag, dumper: SafeDumper, codeobject) -> MappingNode:
        """
        Represent a Object instance as a YAML mapping node.

        This is part of the Output Flow from Python3.9 -> Yaml

        In the Representer Class/Function You must define a mapping
        for the code to be created from the yaml markup

        Args:
            tag (str) : tag to assign object in yaml file
            codeobject (str): python code in a single object
        """
        #tag = "!Repo:"
        return dumper.represent_mapping(tag, codeobject.__dict__)

    def _loader(self, loader: Loader, node: yaml.nodes.MappingNode):
        """
        Construct an object based on yaml node input
        Part of the flow of YAML -> Python3
        """
        # necessary for pyyaml to load files on windows
        if sys.platform == "win32":
            import pathlib
            pathlib.PosixPath = pathlib.WindowsPath
        return KubernetesYaml(**loader.construct_mapping(node, deep=True))
        

    def _get_dumper(self,constructor, classtobuild):
        """
        Add representers to a YAML serializer.

        Converts Python to Yaml
        """
        safe_dumper = Dumper
        safe_dumper.add_representer(classtobuild, constructor)
        return safe_dumper
 
    def _get_loader(self, tag, constructor):
        """
        Add constructors to PyYAML loader.

        Converts Yaml to Python
        Args:
            tags (str): the tag to use to mark the yaml object in the file
            constructor (function): the constructor function to call
        """
        loader = Loader
        loader.add_constructor(tag,constructor)
        return loader
    
    def _loadyaml(self,tag, filelocation:Path):
        """
        Loads the masterlist.yaml into Masterlist.data
        Yaml -> Python3

        Args:
            masterlistfile (str): The file to load as masterlist, defaults to masterlist.yaml
        """
        try:
            #open the yml
            # feed the tag and the constructor method to call
            return yaml.load(open(filelocation, 'rb'), 
                Loader=self._get_loader(tag, self._loader))
        except Exception:
            errorlogger("[-] ERROR: Could not load .yml file {filelocation.stem}")

    def _writeyaml(self,filepath, pythoncode, classtype,filemode="w"):
        """
        Creates a New file
        remember to assign data to the file with
        
        >>> thing = yamlconstructor(filepath)
        >>> thing._writenewstorage(pythoncodeobject)

        Args: 
            pythoncode (Object): an instance of a python object to transform to YAML
            filemode (str) : File Mode To open File with. set to append by default
        """
        try:
            with open(filepath, filemode) as stream:
                stream.write(yaml.dump(pythoncode,
                        Dumper=self._get_dumper(self._representer,classtype)))
        except Exception:
            errorlogger("[-] ERROR: Could not Write .yml file, check the logs!")


class Deployment():
    """
    Base Class for all the attributes required on both the CTFd side and Repository side
    Represents the challenge.yml as exists in the folder for that specific challenge

    Represents a Challenge Folder
    
    Contents of a Challenge Folder:
        handouts: File or Folder
        solution: File or Folder 
        challenge.yaml

    Args:
        yamlfile        (Path): filepath of challenge.yaml
        category        (str):  category to assign to, currently set as folder name
                                needs to be set by yaml tag
        handout         (Path)
        solution        (Path)
    """
    def __init__(self,
            category,
            handout,
            solution,
            readme
            ):
        self.tag = "!Challenge:"
        self.readme = readme
        self.category = category
        #self.deployment         = deployment
        self.solution = solution
        self.handout  = handout

        # this is set after syncing by the ctfd server, it increments by one per
        # challenge upload so it's predictable
        self.id = int

    def _initdeployment(self,**kwargs):
        """
        Unpacks a dict representation of the .yaml

        The structure is simple and only has two levels, and no stored code

        >>> asdf = Deployment(filepath)
        >>> print(asdf.category)
        >>> 'Forensics'

        The new challenge name is created by:

        >>> self.__name = "Challenge_" + str(hashlib.sha256(self.name))
        >>> self.__qualname__ = "Challenge_" + str(hashlib.sha256(self.name))
        
        Resulting in a name similar to 
        Args:
            **entries (dict): Dict returned from a yaml.load() operation on challenge.yaml
        """
        # internal data
        self.id = str
        self.synched = bool
        self.installed = bool

        self.jsonpayload = {}
        self.scorepayload = {}
        # we have everything preprocessed
        for each in kwargs:
            setattr(self,each,kwargs.get(each))
        # the new classname is defined by the name tag in the Yaml now
        self.internalname = "Challenge_" + str(sha1(self.name.encode("ascii")).hexdigest())
        self.__name = self.internalname
        self.__qualname__ = self.internalname
        yellowboldprint(f'[+] Internal name: {self.internalname}')

class KubernetesManagment(KubernetesYaml):
    def __init__(self):
        """
        
        """
        # Configs can be set in Configuration class directly or using helper
        # utility. If no argument provided, the config will be loaded from
        # default location.
        kubernetes.config.load_kube_config()

    def _init_nginx(self,path:Path):
        """
        from docs/examples

        The nginx yaml resides in $PROJECTROOT/containers/nginx
        """
        with open(path.join(path.dirname(__file__), "nginx-deployment.yaml")) as f:
            dep = yaml.safe_load(f)
            k8s_apps_v1 = client.AppsV1Api()
            resp = k8s_apps_v1.create_namespaced_deployment(
                body=dep, namespace="default")
            print("Deployment created. status='%s'" % resp.metadata.name)

class DockerManagment():
    def __init__(self):
        #connects script to docker on host machine
        client = docker.from_env()
        self.runcontainerdetached = lambda container: client.containers.run(container, detach=True)

    def listallpods(self):
        self.setkubeconfig()
        # Configs can be set in Configuration class directly or using helper utility
        print("Listing pods with their IPs:")
        ret = self.client.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    def watchpodevents(self):
        self.setkubeconfig()
        count = 10
        watcher = watch.Watch()
        for event in watcher.stream(self.client.list_namespace, _request_timeout=60):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))
            count -= 1
            if not count:
                watcher.stop()

    def startcontainerset(self,containerset:dict):
        ''' 
        Starts the set given by params
        '''
        for name,container in containerset.items:
            self.runcontainerdetached(container=containerset[name])

    def runcontainerwithargs(container:str,arglist:list):
        client.containers.run(container, arglist)

    def listcontainers():
        '''
        lists installed containers
        '''
        for container in client.containers.list():
            print(container.name)


    def opencomposefile(docker_config):
        '''
        '''
        with open(docker_config, 'r') as ymlfile:
            docker_config = yaml.load(ymlfile)

    def writecomposefile(docker_config,newyamldata):
        with open(docker_config, 'w') as newconf:
            yaml.dump(docker_config, newyamldata, default_flow_style=False)

#if __name__ == '__main__':
listofimportantyamlfiles = ["deployment.yaml","service.yaml"]
packageofyaml = {}
packageofcode = {}
for importantyaml in listofimportantyamlfiles:
    # get path
    yamlpath = getpath(importantyaml)
    # load file
    newyaml = Yaml().loadyaml(yamlpath)
    # add to output
    packageofyaml[importantyaml] = newyaml

for importantyaml in listofimportantyamlfiles:
    # get path
    yamlpath = getpath(importantyaml)
    # load file WITH CONSTRUCTOR FOR CODE
    newpythoncode = Constructor()._loadyaml(getpath(importantyaml))
    # add to output
    packageofcode[importantyaml] = newpythoncode