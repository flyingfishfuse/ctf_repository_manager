import fire
import os
from pathlib import Path
import configparser
PWD = os.path.realpath(".")
################################################################
# config contents
################################################################
#[Default]
#file_path=/home/moop/Desktop/work/ctf_deployment_manager/extra/tutorials/
#authtoken = acab42069lolz
#allowedcategories = crypto,forensics,miscellaneous,osint,reversing,testcat
#allowdeployments=True
#masterlistlocation=/home/moop/desktop/work/ctf_deployment_manager/data/CTFd/masterlist.yaml


class Test1():
    # things in the __init__ run when the thing is called
    def __init__(self):
        self.msg = "test1"

    def speak(self, blarp:str, test_var:str=""):
        ''' makes a word be a word babeh'''
        self.test_var_name = test_var
        print(blarp)
        print(self.msg)
        print(self.test_var_name)

class Test2():
    def __init__(self):
        self.msg = "test asdfwqer"

    def speak(self, test_var):
        print(self.msg)

    def test(self):
        print("something testy")
class UITestConfig():
    def __init__(self,file_path:Path= Path("")):
        self.config = configparser.ConfigParser()
        # we only need one section for this app so far
        self.config_section = "Default"
        #self._read_config(configpath)
        # if path not supplied use default
        if file_path== Path(""):
            self.cfgfilepath = str(Path(PWD, 'config.cfg'))
        else:
            self.cfgfilepath = file_path

    def readconfig(self,configpath:Path):
        ''' user interface to config class'''
        self._read_config(configpath)

    def _read_config(self,location:Path):
        '''internal usage
        Reads from config and sets data to class attribute'''
        try:
            self.cfgfilepath = Path(os.path.abspath(location))
            #print(f"[+] Reading Config {location}")
            self.config.read(filenames=self.cfgfilepath)
        except Exception:
            print("[-] FAILED: Reading Config --- ")

    def write_config_value(self,key:str,value:str):
        '''write value to configuration file'''
        # Check if the key exists in the specified section
        #if self.config.has_option(self.config_section, value):
            # Update the existing key's value
        self.config.set(self.config_section, key, value)
        print(f"Updated '{key}' in '{self.config_section}' to '{value}'")
        

    def read_config_value(self,value:str):
        '''read value from configuration file'''
        config_value = self.config.get('default',option=value)
        return config_value


    def write_whole_config(self):
        '''write whole configuration file'''
        #if config is not specified, use default
        with open(self.cfgfilepath, 'w') as configfile:
            self.config.write(configfile)

#new_config = UITestConfig(Path("/home/moop/Desktop/work/ctf_repository_manager/extra/tutorials/tutorial_config.cfg"))

class Test3():
    def __init__(self, **kwargs):
        print("1: --------------------------------")
        print("1: Testing Test3: calling from code __init__")
        for key, value in kwargs.items():
            print("1: %s == %s" % (key, value))
        print("1: --------------------------------")    

    def test1(**important_items):
        print("2: --------------------------------")
        print("2: Testing Test3: inside Test3.test1()")
        print("2: " + str(important_items['repository']))
        print("2: " + str(important_items['masterlist']))
        print("2: --------------------------------")
# Driver code
print("3: --------------------------------")
print("3: Testing Test3: calling from code top level")
path1 = Path("./repository").resolve
path2 = Path("./masterlist").resolve
Test3(repository=path1, masterlist=path2)
print("3: --------------------------------")

if __name__ == "__main__":
    #fire.Fire({
    #    "test1"     : Test1,
    #    "test2"   : Test2
    #})
    print("4: --------------------------------")
    print("4: Testing Test3: calling from CLI")
    fire.Fire(Test3)
    print("4: --------------------------------")
# We can instantiate it as follows: python example.py --name="Sherrerd Hall"
#Arguments to other functions may be passed positionally or by name using flag syntax.
#To instantiate a Building and then run the climb_stairs function, the following commands are all valid:

#$ python example.py --name="Sherrerd Hall" --stories=3 climb_stairs 10
#$ python example.py --name="Sherrerd Hall" climb_stairs --stairs_per_story=10
#$ python example.py --name="Sherrerd Hall" climb_stairs --stairs-per-story 10
#$ python example.py climb-stairs --stairs-per-story 10 --name="Sherrerd Hall"