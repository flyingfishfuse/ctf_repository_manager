# deployment managment
from kubernetes import client, config, watch
import docker,yaml

class KubernetesConfig(client.Configuration):
    """
    Wraper for kubernetes.client.configuration
        By default, kubectl looks for a file named config 
        in the $HOME/.kube directory. You can specify other 
        kubeconfig files by setting the KUBECONFIG 
        environment variable
    """
    def __init__(self,kubeconfigpath:Path):
        """
        currently in version 1.5, we set the KUBECONFIG environmment variable 
        in the top level file __main__.py in the root project directory

        if it isnt set, the module is being used in standalone mode and must be set
        manually by providing a dict to kubecopnfigpath

        >>>    {
        >>>        KUBECONFIG  : ""
        >>>        context     : ""
        >>>    }

        Args:
            kubeconfigpath (Path): Path to kubeconfig folder
        """
        self.kubeconfigpath = Path
        if "KUBECONFIG" in os.environ():
            self.kubeconfigpath = os.environ.get("KUBECONFIG")
            infolog(f"[+] KUBECONFIG environment variable set as \n {self.kubeconfigpath}")
        elif "KUBECONFIG" not in os.environ():
            self.setkubernetesenvironment(kubeconfigpath)
            infolog(f"[?] KUBECONFIG environment variable is not set")
            infolog(f"[+] KUBECONFIG environment variable set as \n {self.kubeconfigpath}")
 
    def setkubernetesenvironment(self,configdict:dict,useenv = True):
        """
        sets kubernetes environment
        if useenv is set to True, uses system environment variables
        for setting config, otherwise
        if set to false, uses provided dict
            {
                KUBECONFIG  : ""
                context     : ""
            }
        """
        if useenv:
            config_file = os.environ.get("KUBECONFIG", KUBE_CONFIG_PATH),
            context = os.environ.get("KUBECONTEXT")
        elif not useenv:
            config_file = configdict.get("KUBECONFIG")
            context = configdict.get("context")

        self.load_kube_config(
            config_file,
            context,
        )

    def setkubeconnection(self,
                      authtoken = "YOUR_TOKEN",
                      authorization = "Bearer",
                      host = "http://192.168.1.1:8080"):
        """
        """

        # Defining host is optional and default to http://localhost
        #configuration.host = "http://localhost"

        self.host = host
        self.api_key_prefix['authorization'] = authorization
        self.api_key['authorization'] = authtoken
        v1 = client.CoreV1Api()

class KubernetesManagment():
    def __init__(self):
        """
        
        """
        # Configs can be set in Configuration class directly or using helper
        # utility. If no argument provided, the config will be loaded from
        # default location.
        config.load_kube_config()
    
    def get_k8s_nodes(exclude_node_label_key=app_config["EXCLUDE_NODE_LABEL_KEY"]):
        """
        Returns a list of kubernetes nodes
        """

        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                raise Exception("Could not configure kubernetes python client")

        k8s_api = client.CoreV1Api()
        infolog("Getting k8s nodes...")
        response = k8s_api.list_node()
        if exclude_node_label_key is not None:
            nodes = []
            for node in response.items:
                if exclude_node_label_key not in node.metadata.labels:
                    nodes.append(node)
            response.items = nodes
        infolog.info("Current k8s node count is {}".format(len(response.items)))
        return response.items 

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
