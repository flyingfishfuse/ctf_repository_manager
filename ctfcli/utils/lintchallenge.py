import subprocess
import yaml
import subprocess
from pathlib import Path
from utils.utils import errorlogger,redprint,DEBUG
from utils.utils import debugblue,debuggreen,debugred,debugyellow
class Linter():
    """

    I wasnt thinking the best when I wrote this so its pretty procedural 
    
    Class to lint challenge.yaml files to decrease size of Challenge class
    codebase

    Challenge.yaml files are NOT processed by ClassConstructor.py
    They are NOT automatically converted into code, they follow a 
    different pipeline where the files are suspect and require linting

    if the directory contains a metadata.yaml or kubernetes spec
    its for a deployment and should be handled differently
    """
    def __init__(self,
                #kwargs:dict,
                togglevisibility=True):
        debuggreen("[DEBUG] Creating Linter() Class")
        self.jsonpayload = {}
        self.scorepayload = {}
        # the base repo has too few challenges to justify making any invisible
        # right from the get go, so its set to true by default
        self.toggle = togglevisibility
        # BSIDES STUFF ONLY
        # This is the standard metadata for a challenge with a web component.
        # In terms of file structure, please also have the following:
        #
        # - A challenge/ folder with everything needed to create the challenge assets
        # - A distfiles/ folder which contains all files (or symlinks to files) that
        #   will be attached to the challenge
        # - A solution/ folder with a working solution to the challenge (or a README.md
        #   file documenting the solution)
        self.name:dict = None
        self.category:dict = None
        self.description:dict = None
        self.scorepayload:dict = None
        self.flags:dict = None
        self.topics:dict = None
        self.tags:dict = None
        self.files:dict = None
        self.hints:dict = None
        self.requirements:dict = None
        self.max_attempts:dict = None
        self.extratags:dict = None
        self.notes:dict = None
        self.author:dict = None
        self.typeof:dict = None
        self.extra:dict = None
        wat = ['replicas',
               'environ',
               ]
        self.deploymentfields = [
                            'port', 'protocol', 'use_http_loadbalancer',
                            "image","host","connection_info" 
                            ]
        self.depfieldstype = {
                            'port':[int], 
                            'protocol':[str], 
                            'use_http_loadbalancer':[str],
                            "image": [str],
                            "host":[str],
                            "connection_info":[str]
                        }
        self.flagstags = ['flag','flags']
        self.reqfieldstypes = {
                "name": [str], 
                "category": [str], 
                "description":[str],
                'value':[int], 
                "version":[str,int],
                'flag':[str,list],
                'flags':[str,list],
                "state":[str]
                }

        self.requiredfields = [
            "name", "category", "description", 
            'value', "version", "type",# "extra",
            #"state"
            ]
        self.optionalfields = ["topics","hints","max_attempts","requirements",'notes', 'tags','scoreboard_name','author','files']
        #Required sections get the "pop()" function 
        # a KeyError will be raised if the key does not exist

    def lintchallengeyaml(self,dictfromyaml:dict)-> dict:
        """
        Lints a challenge.yaml and spits out a dict
        
        >>> linter = Linter()
        >>> outputdict = linter.lintchallengeyaml(yamlfilelocation)
        >>> newchallenge = Challenge(**outputdict)
        """
        try:
            debuggreen("[DEBUG] linting challenge yaml file")

            #process required fields
            requirementsdict = self.extractrequired(dictfromyaml)
            #did a shitty hack in the scope above to push the category into the dict
            # this value needs to be assigned by the yaml eventually
            self._processcategory(requirementsdict)
            self._processrequired(requirementsdict)

            #process optional fields
            optionaldict = self.extractoptional(dictfromyaml)
            self.lintoptional(optionaldict)

            # ssets everything into self.jsonpayload
            self.setpayload()
            return self.jsonpayload
        except Exception:
            errorlogger("[-] ERROR linting challenge yaml \n ")

    def validatetags(self, tag, dictfromyaml:dict, template:dict):
        """
        Checks if field data is of a type allowed by the spec

        Args:
            tag             (str):  tag to validate
            dictfromyaml    (dict): dict to validate
            template        (dict): template to validate against
        """
        debuggreen("[DEBUG] validating tags in linter")
        # get the types allowed for that tag
        allowedtagtypes = template.get(tag)
        # get the tag contents and compare the two
        # check to see if the tag is in the list of things REQUIRED!
        if type(dictfromyaml.get(tag)) in allowedtagtypes:
            return True
        else:
            return False

    def validaterequired(self,tag, dictfromyaml:dict, template:dict):
        """
        Validates tag field types for required components of challenge.yaml
        """
        debuggreen("[DEBUG] validating required tags in linter")
        #check if the challenge is MISSING any required tags!
        if type(dictfromyaml.get(tag)) not in self.requiredtagtypes:
            return False
        else:
            return True

    def extractrequired(self,dictfromyaml:dict):
        """
        POPs all the required, thorws an exception if they arent present
        """
        try:
            debuggreen("[DEBUG] extracting required tags in linter")
            reqdict = {}
            # some challenges have no state assigned
            self._processstate(dictfromyaml)
            # field with more than one tag for the same data
            self._processflags(dictfromyaml)
            # type is higher level important
            # required flags are indicated by its existance
            self._processtype(dictfromyaml)
            if self.typeof.get("typeof") == "dynamic":
                self.requiredfields.append("extra")
            
            # finally, process the required fields
            for each in self.requiredfields:
                if dictfromyaml.get(each) != None:
                    reqdict.update({each: dictfromyaml.pop(each)})
            return reqdict
        except Exception:
            errorlogger("[-] ERROR: Failed to validate Required Fields \n")

    def extractoptional(self, optionaldict:dict):
        """
        """
        debuggreen("[DEBUG] extracting optional tags in linter")
        self.optionalfields = ['author',"topics","hints","max_attempts",
                               "requirements",'notes', 'tags',
                               'scoreboard_name','files']
        try:
            optdict = {}
            for tag in self.optionalfields:
                tagdata = optionaldict.get(tag)
                if tagdata != None:
                    optdict.update({tag: tagdata})
            return optdict
        except Exception:
            errorlogger("[-] ERROR: Failed to validate Required Fields \n")

    def _processvalue(self,requirementsdict:dict):
        """
        
        """ 
        try:
            debuggreen("[DEBUG] processing value in linter")
            tagdata = requirementsdict.pop('value')
            if (type(tagdata) != int):
                redprint("[-] ERROR: Value field should be an integer, skipping challenge \n")
                raise ValueError
            else:
                self.value = {'value':tagdata}
        except Exception:
            errorlogger("[-] ERROR: Failed to validate Required Fields \n")

    def _processtype(self,requirementsdict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing score fields in linter")
        tagdata = requirementsdict.pop('type')
        if tagdata in ["static","standard","dynamic"]:
            self.typeof = {"typeof" : tagdata}

    def _processscore(self,requirementsdict:dict):
        """
        
        """
        try:
            debuggreen("[DEBUG] processing score fields in linter")
            #self.typeof = requirementsdict.pop('type')
            # dynamic challenges
            if self.typeof['typeof'] == 'dynamic':
                # have the extra field
                self.extra:dict = requirementsdict.pop("extra")
                for each in self.extra:
                    if (type(self.extra.get(each)) != int):
                        redprint(f"[-] ERROR: {each} field should be an integer, skipping challenge \n")
                        raise ValueError
                    else:
                        self.scorepayload = {
                            **self.value,
                            'initial': self.extra['initial'],
                            'decay'  : self.extra['decay'],
                            'minimum': self.extra['minimum']
                            }
            # static challenges only have the "value" field
            elif (self.typeof.get('typeof') == 'static') or (self.typeof.get('typeof') == 'standard'):
                self.scorepayload = self.value #{'value' : self.value} 
        except Exception:
            errorlogger("[-] ERROR: Score data does not match specification, skipping challenge! \n")

    def _processstate(self, dictfromyaml:dict):
        """
        Process state tag from challenge yaml file
        """
        debuggreen("[DEBUG] processing visibility state in linter")
        # check state field
        # we should set state to visible unless self.toggle is set to false
        # then we use the value in the yaml file
        if dictfromyaml.get("state") != None:
            state = dictfromyaml.pop("state")
        #if state != None:
            # they want to toggle all challenges to visible
            if state == 'hidden' and self.toggle == True:
                self.state =  {"state":'visible'}
            # no toggle, just assignment
            else:
                self.state = {"state":state}
        # there was no "state" field in the yaml
        # presume its gor hidden prereqs?
        else:
            self.state = {"state": 'hidden'}

    def _processname(self,requirementsdict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing name in linter")
        tagdata = requirementsdict.pop("name")
        self.name = {"name":tagdata}

    def _processdescription(self,requirementsdict):
        """
        
        """
        debuggreen("[DEBUG] processing description in linter")
        if requirementsdict.get('description') != None:
            tagdata = requirementsdict.pop("description")
            self.description = {"description":tagdata}
        else:
            debugred("[DEBUG] no Version tag in yaml")
            self.description = {"description": "EMPTY NOT IN YAML"}

    def _processversion(self,requirementsdict):
        """
        
        """
        debuggreen("[DEBUG] processing version in linter")
        if requirementsdict.get('version') != None:
            tagdata = requirementsdict.pop("version")
            self.version = {"version":tagdata}
        # if version is not present in the yaml file
        else:
            debugred("[DEBUG] no Version tag in yaml")
            self.version = {"version": "0.1"}
            #raise Exception

    def _processintitem(self, tag:str,yamldict:dict):
        """
        UNUSED, FUTURE
        checks existance of str item, adds to output if valid
        """
        debuggreen("[DEBUG] processing tag in linter")
        if yamldict.get(tag) != None:
            tagdata = yamldict.pop(tag)
            setattr(self,tag, {tag: tagdata})
        else:
            debugred(f"[DEBUG] no {tag} tag in yaml")
            if DEBUG:
                setattr(self,tag,{tag: "field was empty during loading"})
            else:
                raise Exception

    def _processstritem(self, tag:str, yamldict:dict):
        """
        UNUSED, FUTURE
        checks existance of str item, adds to output if valid
        """
        debuggreen("[DEBUG] processing tag in linter")
        if yamldict.get(tag) != None:
            tagdata = yamldict.pop(tag)
            self.category = {tag: tagdata}
        else:
            debugred(f"[DEBUG] no {tag} tag in yaml")
            raise Exception

    def _processcategory(self, requirementsdict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing category in linter")
        # dangly bit for future additions
        if requirementsdict.get("category") != None:
            tagdata = requirementsdict.pop("category")
            self.category = {"category": tagdata}
        else:
            debugred("[DEBUG] no category tag in yaml")
            raise Exception

    def _processflags(self,requirementsdict:dict):
        """
        
        """
        self.flagstemplate = {
                "content":str,
                #"data":str,
                "type":str, #"static",
                "challenge":str#int
            }
        flagsdict = {}
        try:
            debuggreen("[DEBUG] processing flags in linter")
            try:
                flagsdata = requirementsdict.pop("flags")
            except:
                try:
                    flagsdata = requirementsdict.pop("flag")
                except:
                    errorlogger("[-] ERROR: Flags missing from challenge, rejecting")
            #single flag, inline with tag
            if (type(flagsdata) == str):
                self.flagstemplate["content"] = flagsdata
                self.flagstemplate["type"] = "static"
                flagsdict.update(self.flagstemplate)
            #multiple flags, on thier own lines
            elif type(flagsdata) == list:
                for flag in flagsdata:
                    # special flags
                    if type(flag) == dict:
                        flagsdict.update(flag)
                    #string flag on its own line
                    elif (type(flag) == str):
                        self.flagstemplate["content"] = flagsdata[0]
                        self.flagstemplate["type"] = "static"
                        flagsdict.update(self.flagstemplate)
            # multiple flags
            elif type(flagsdata) == dict:
                flagsdict.update(flagsdict)        
        # finally, assign everything to dict, it should all be a dict of dicts now
            self.flags = {"flags": flagsdict }
        except Exception:
            errorlogger("[-] ERROR: flags do not conform to spec")

    def _processtopics(self, optionaldict:dict):
        """
        
        """
        try:
            debuggreen("[DEBUG] processing topics in linter")
            if optionaldict.get("topics"):
                tagdata = optionaldict.pop("topics")
                self.topics = {"topics": tagdata }
        except Exception:
            errorlogger("[-] ERROR: flags do not conform to spec")

    def _processtags(self, optionaldict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing tags in linter")
        tagdata = optionaldict.pop("tags")
        self.tags = {"tags":tagdata}

    def _processfiles(self, optionaldict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing files in linter")
        tagdata = optionaldict.pop("files")
        self.files = {"files":tagdata}

    def _processhints(self, optionaldict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing hints in linter")
        tagdata = optionaldict.pop("hints")
        self.hints = {"hints":tagdata}

    def _processrequirements(self,optionaldict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing requirements in linter")
        tagdata = optionaldict.pop("requirements")
        self.requirements = {"requirements":tagdata}

    def _processauthor(self,optionaldict):
        """
        
        """
        debuggreen("[DEBUG] processing author in linter")
        tagdata = optionaldict.pop("author")
        self.author = {"author":tagdata}

    def _processnotes(self,optionaldict:dict):
        """
        
        """
        debuggreen("[DEBUG] processing notes in linter")
        tagdata = optionaldict.pop("notes")
        self.notes = {"notes":tagdata}

    def _processattempts(self,optionaldict:dict):
        """
        
        """
        try:
            debuggreen("[DEBUG] processing max_attempts in linter")
            tagdata = optionaldict.get("max_attempts")     
            if (type(tagdata) != int):
                redprint("[-] Attempts field should be an integer, skipping challenge \n")
                raise ValueError
            else:
                self.max_attempts == {"max_attempts": optionaldict.pop('max_attempts')}
        except Exception:
            errorlogger("[-] ERROR! Skipping challenge \n ")

    def _processrequired(self,requirementsdict:dict):
        """
        process required challenge fields from challenge.yaml
        as loaded by pyyaml
            # check for bad value in challenge points
            if type(dictfromyaml.get('value')) != int:
                raise TypeError
            else:
                self.value = dictfromyaml.pop('value')
        Output is a Dict suitable for loading into a Challenge() Class
        by the way of challenge = Challenge(**filtereddict)
        """
        try:
            #for tag in self.requiredfields:
            for tag in requirementsdict.copy():
                length = len(requirementsdict)
                debuggreen(f"[DEBUG] requirementsdict length {length} ")
                if (length == 0):
                    break
                    #continue
                elif (length > 0):
                    tagdata = requirementsdict.get(tag)
                    debuggreen(f"[DEBUG] processing tag  {tag} : {tagdata} ")
                    # type determines score and currently the only field 
                    # requiring extra values for certain tags
                    if tag =='value':
                        self._processvalue(requirementsdict)
                        self._processscore(requirementsdict)
                    elif tag =='name':
                        self._processname(requirementsdict)
                    elif tag =='flags' or tag == "flags":
                        self._processflags(requirementsdict)
                    elif tag =='description':
                        self._processdescription(requirementsdict)

                    elif tag =='version':
                        self._processversion(requirementsdict)                    
                    else:
                        pass                        
                    #    self.jsonpayload[tag] = requirementsdict.pop(tag)
            #errorlogger("[-] Tag not in specification, rejecting challenge entry \n")
        except Exception:
            errorlogger(f"[-] Challenge.yaml does not conform to specification, rejecting.\n [-] Missing tag: {tag} \n")                
    
    def lintoptional(self,optionaldict:dict):
        try:
            for tag in optionaldict.copy():
                length = len(optionaldict)
                debuggreen(f"[DEBUG] requirementsdict length {length} ")
                if (length == 0):
                    break
                    #continue
                elif (length > 0):
                    tagdata = optionaldict.get(tag)
                    debuggreen(f"[DEBUG] processing tag  {tag} : {tagdata} ")
                    #if tag == 'state':
                        #self._processstate(optionaldict)
                    if tag == 'author':
                        self._processauthor(optionaldict)
                    elif tag == "max_attempts":
                        self._processattempts(optionaldict)
                    elif tag =="topics":
                        self._processtopics(optionaldict)
                    elif tag =="tags":
                        self._processtags(optionaldict)
                    elif tag =="files":
                        # y know what... just tar everything
                        #self._processfiles(optionaldict)
                        pass
                    elif tag =="hints":
                        self._processhints(optionaldict)
                    elif tag =="requirements":
                        self._processrequirements(optionaldict)
                    elif tag =="notes":
                        self._processnotes(optionaldict)
                
                    else:
                        pass
        except Exception:
            errorlogger(f"[-] ERROR: tag data not valid: {tag}")
    
    def setpayload(self):
        debuggreen("[DEBUG] Setting payload in linter ")
        # set base challenge payload
        templatelist = [self.name,
                        self.category,
                        self.description,
                        self.scorepayload,
                        self.flags ,
                        self.topics,
                        self.tags,
                        #self.files,
                        self.hints,
                        self.requirements,
                        self.max_attempts,
                        self.notes,
                        self.author,
                        self.version,
                        self.state,
                        self.typeof,
                        ]
        #print(templatelist)
        asdf = [thing for thing in templatelist if thing != None]
        print(asdf)
        for yamltag in asdf:
            if yamltag != None:
                self.jsonpayload.update(yamltag)

    def lintdockerstuff(self,dictofstuff:dict=None,pathtothing:Path=None):
        """
        Lints dockerfile and deplyment items
        """
        # Check that the image field and Dockerfile match
        if (Path(pathtothing).parent / "Dockerfile").is_file() and dictofstuff.get("image") != ".":
            print("Dockerfile exists but image field does not point to it")
            exit(1)

        # Check that Dockerfile exists and is EXPOSE'ing a port
        if dictofstuff.get("image") == ".":
            try:
                dockerfile = (Path(pathtothing).parent / "Dockerfile").open().read()
            except FileNotFoundError:
                print("Dockerfile specified in 'image' field but no Dockerfile found")
                exit(1)

            if "EXPOSE" not in dockerfile:
                print("Dockerfile missing EXPOSE")
                exit(1)

            # Check Dockerfile with hadolint
            proc = subprocess.run(
                ["docker", "run", "--rm", "-i", "hadolint/hadolint"],
                input=dockerfile.encode(),
            )
            if proc.returncode != 0:
                print("Hadolint found Dockerfile lint issues, please resolve")
                exit(1)
