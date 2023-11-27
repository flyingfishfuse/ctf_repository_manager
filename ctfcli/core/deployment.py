from ctfcli.utils.utils import infolog,errorlogger,greenprint,redprint,yellowboldprint
from ctfcli.core.yamlstuff import Yaml,KubernetesYaml

import os
from pathlib import Path
from hashlib import sha1


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
            deployment:Path,
            service:Path,
            readme
            ):
        self.tag = "!Deployment:"
        self.readme = readme
        self.category = category
        self.solution = solution
        self.handout  = handout
         
         # here, we deviate from the challenge class and include
         # deployment and service yaml files
        self.deployment = deployment
        self.service = service

        # this is set after syncing by the ctfd server, it increments by one per
        # challenge upload so it's predictable
        self.id = int

    def _initchallenge(self,**kwargs):
        """
        Unpacks a dict representation of the challenge.yaml into
        The Challenge() Class, this is ONLY for challenge.yaml

        The structure is simple and only has two levels, and no stored code

        >>> asdf = Challenge(filepath)
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
        self.internalname = "Deployment_" + str(sha1(self.name.encode("ascii")).hexdigest())
        self.__name = self.internalname
        self.__qualname__ = self.internalname
        yellowboldprint(f'[+] Internal name: {self.internalname}')

