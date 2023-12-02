    LINKS/CREDITS ARE IN LICENSE, README IS FOR INFORMATION

# CTFD / CTFCLI_rewrite based ctf in a box with automated docker or kubernetes deployment ... eventually
# PENTEST SANDBOX

    this is an all in one setup script for a docker/kubernetes cluster
    specifically, it creates a pentesting sandbox/ctfd instance

    I am "shaking the rug out" as it were, I got it to a functional state and moved to
    version 1.x adding the deployment code but took a hiatus to focus on my life and
    in that time I forgot where the hell I was at what the hell I was doing so please
    excuse the mess while I fix the borked-ed-ness

# DAILY PLAN

    finish various functions

    Starting the deployment code, this will essentially become the backend 
    to a ctfd/electron interface

    ctfcli moved to top level scope, it will become the deployment manager 
    in addition to installing challenges to ctfd

![terminal output](https://raw.githubusercontent.com/mister-hai/sandboxy/master/extra/docs/ctfd1.png)
![terminal output](https://raw.githubusercontent.com/mister-hai/sandboxy/master/extra/docs/test1.png)

![platform display](https://raw.githubusercontent.com/mister-hai/sandboxy/master/extra/docs/startscript.png))

# CTFCLI
    to create an initial repository,you must structure it as the following
```
        folder: ctfcli tool
        folder: data
            folder: CTFd
                folder: challenges
                    folder: category A
                        folder: challenge_name
                            file: challenge.yaml
                            file: (dependant) deployment.yaml
                            folder: handout
                                file: handout file/s
                            folder: soution
                                file: solution file/s
                    folder: category B
                    folder: ... so on and so on
                file:   masterlist.yaml

            If necessary, the following structure is needed for a deployment
            challenge folder
                challenge.yaml
                DOCKERFILE (If required)
                deployment folder
                    deployment.yaml
                    service.yaml
                    dockerfile
                handout folder
                    handout file/s
                soution folder
                    solution file/s
```
# usage

Assumptions:

first assumption
> the folder of the tool itself is in this project with it's particular structure of folders
    and files, or you are explicitly telling the program where the folder containing a repository
    is located by changing the relevant line in the config.cfg

second assumption:
> The config file is either alongside the tool folder (not inside it although that may be an option later)
or you are explicitly pointing the tool to the location of a config.cfg on runtime

The software will store ALL the information (minus binary information, until V1.x) about the repository
and configuration in the `masterlist.yaml` upon usage of the `init` command. From that point on if 
the infrastructure or repository need to change, a new masterlist needs to be created.

commands:

if you are running the tool outside of the context of this repository (custom repo) or not 
in the same directory as the challenge folder you need to use the commands :

```bash
# maybe not these anymore?
#export CONFIG_LOCATION=<full_path_goes_here>
#export PROJECT_ROOT=<full_path_goes_here>
#export CHALLENGE_REPO_ROOT=<full_path_goes_here>
python3 ./ctfcli init --config=<full_path_goes_here>

```

This will scan the folder and generate a masterfile.yaml of the challenge contents
It creates a yaml representation of python code for tracking, validation and to "load"
the structure of the ctf repository into the application for later use without requiring 
scanning a second time. if anything changes in the folder with the challenges this app
will know and ignore it until scanned again.

---
2. This will still require the challenges be organized according to the specification above
---

3. The first time you run this tool it will ALWAYS look for a config file NEXT to the 
tool folder in the SAME directory as the tool folder itself. If one is not present it will
exit without running

The masterlist.yaml has already been generated for this repo and the only thing you need to do
is change the contents of the config and run the commands:

```bash
python3 ./ctfcli syncrepository

```
---

4. This software expects that the deployment data is alongside the tool so 
please have a look around the project and become familiar with it so you
may tailor it to your needs. The reason for this is because the `start.sh`
script will zip and encode the whole project into base64 then append it to 
itself for easy transmission. This behavior is similar to malware movement
so be sure your AV/IPS does not delete it :p
---

5. If you are just planning on using this software as-is, you run the commands:

 ```bash
chmod +x ./start.sh
./start.sh deploy
# then you run the ctfcli tool
ctfcli help
```
---
# kubernetes config


kubernetes config information is loaded from the shell environment with the following code:

```python
kube_config.load_kube_config(
        config_file=os.environ.get("KUBECONFIG", KUBE_CONFIG_PATH),
        context=os.environ.get("KUBECONTEXT"),
    )
```
to change the directory you must change the environment variable
    
See here: https://github.com/kubernetes-incubator/client-python/blob/436351b027df2673869ee00e0ff5589e6b3e2b7d/kubernetes/config/kube_config.py#L283

config.load_kube_config(context='some context')

If you are not familiar with Kubernetes contexts, Kubernetes stores your configuration under ~/.kube/config (default location). In it you will find context definition for every cluster you may have access to. A field called current-context defines your current context.

You can issue the following commands:
    
    kubectl config current-context to see the current context
    
    kubectl config view to view all the configuration

The KUBECONFIG environment variable holds a list of kubeconfig files. 
For Linux and Mac, the list is colon-delimited. 
For Windows, the list is semicolon-delimited. 

The KUBECONFIG environment variable is not required. 
If the KUBECONFIG environment variable doesn't exist, 
kubectl uses the default kubeconfig file, $HOME/.kube/config.

If the KUBECONFIG environment variable does exist, 
kubectl uses an effective configuration that is the result of 
merging the files listed in the KUBECONFIG environment variable.

    ! letsencrypt should be used only if a domain name is available !
                run init_letsencrypt.sh FIRST AND ONLY ONCE!
    ! letsencrypt should be used only if a domain name is available !

            
            - moar ctfd challenges here
                https://github.com/bsidessf

            - oohhh shiny!
                https://github.com/cliffe/SecGen

        How to setup your public hostname for letsencrypt to function
            https://kerneltalks.com/howto/how-to-setup-domain-name-in-linux-server/
            https://raw.githubusercontent.com/wmnnd/nginx-certbot/master/init-letsencrypt.sh


# SYSTEMPREP

        Instructions for setting up a server from scratch can be found here

        extras/ServerSetup.MD

# Config contents example
```conf
[default]
username=moop
password=password
authtoken = faketoken12345
#token=1712d60a762e1bf82bf8374d2b4e26a93b30dde3063ce51dac68fce30c4cace7
# this is without schema, only the domain
#url=127.0.0.1:8000
url=ctfd.moopbox.wtf
categories=crypto,osint,exploitation,reversing,web,forensics,scripting,networking,linux,miscellaneous
hints=True
masterlistlocation=home/moop/desktop/work/ctf_deployment_manager/data/CTFd/masterlist.yaml
projectroot=home/moop/desktop/work/ctf_deployment_manager/
```

# certbot initiation
    
    Docker compose command before "docker-compose -f main-compose.yaml up"
    docker-compose -f main-compose.yaml run --rm -v "./data/certbot/conf:/etc/letsencrypt" -v "./data/certbot/www:/var/www/certbot" -v "./data/log/letsencrypt:/var/log/letsencrypt" nginx --entrypoint certbot --nginx --noninteractive --agree-tos --register-unsafely-without-email -d fightbiscuits.firewall-gateway.net 

# KCTF INSTRUCTIONS
    
    After installing kctf
    in a terminal, in the main project directory
    
        source kctf/activate

            - activates the kctf environment allowing you to upload
                challenge.yaml files from kubernetes deployments

        kctf cluster create local-cluster --start --type kind

            - creates a "kind" cluster, kind is a docker driver
                for kubernetes that has recently been deprecated
                although will remain supporteted as a containerd 
                abstraction
    
    FROM THE MAIN PROJECT DIRECTORY:
        perform the following sort of commands to move the kubernetes 
        challenges to the kctf templates folder
    
        cp -ar ./challengedir/UIUCTF-2021-Public/web/* ./kctf/challenge-templates/
        cp -ar ./challengedir/UIUCTF-2021-Public/pwn/* ./kctf/challenge-templates/

    Now you can create the challenges with kctf
    THE CHALLENGES MUST BE UPLOADED TO CTFD FIRST BEFORE ACTIVATING THE ENVIRONMENT
    This example uses ponydb from the UIUCTF-2021 challenge

        kctf chal create --template ponydb ponydb && cd ponydb
            - creates a folder in the main project directory, alongside kctf and 
                sandboxy and the main repository for CTFd
            - changes shell location to that challenge folder
            - the challenge is created from the template
    
    in that folder run the following command:
    
        kctf chal start

    And you will see the following as output:

        [*] building image in "/home/moop/pwnyide/challenge"
        [*] Image ID "8373-----49fe"
        [*] building image in "/home/moop/pwnyide/healthcheck"
        [*] Image ID "c0b07bb15de------36"
        Image: "kind/challenge:8373f7-----05549fe" with ID "sha256:8373f7b887b741ea-----549fe" not yet present on node "kctf-cluster-control-plane", loading...      
        [*] Image pushed to "kind/challenge:8373f7------549fe"
        Image: "kind/healthcheck:c0b07bb15----337a36" with ID "sha256:c0b----37a36" not yet present on node "kctf-cluster-control-plane", loading...
        [*] Image pushed to "kind/healthcheck:c0b07----337a36"
        challenge.kctf.dev/pwnyide created
    
    CONNECTING TO THE CHALLENGE:
    
    To connect to the challenge, run the following command:

        kctf chal debug port-forward &
    
    You will see the following output:

        moop@fightbiscuits:~/pwnyide$ kctf chal debug port-forward &
        [1] 131556
        moop@fightbiscuits:~/pwnyide$ [*] starting port-forward, ctrl+c to exit
        Forwarding from 127.0.0.1:42743 -> 1337

## Some Notes

    
    Historically the security of user namespace was uncertain. eg: lwn.net/Articles/673597 . 
    If a user, as root inside her own namespace can trick the kernel into allowing an operation
    on the real host, there's privilege escalation. Usual non-user namespaces require explicit
    root (so admin) permission and so run what the admin chose: that's a known risk. A later
    mechanism was added in vanilla kernel: user.max_user_namespaces . When set to 0 user
    namespaces are disabled. The Debian (actually from Ubuntu) patch is still around, even if
    probably obsolete. Maybe for compatibility reasons – A.B Mar 20 '18 at 14:30
	clear


