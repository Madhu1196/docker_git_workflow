import sys
import subprocess
import json
import os
import time


#Provides authentication to gcloud

def generateKeyFile(folder_path):

    KEY_FILE    = os.path.join(folder_path,"gcp.json")
    cmnd = "gcloud auth activate-service-account --key-file {0}".format(KEY_FILE)
    p = subprocess.Popen(cmnd, shell=True)
    output, error = p.communicate()


#Retrieves all necessary data from configs.json

def get_data_from_json(folder_path):

    CONFIG_FILE = os.path.join(folder_path,"configs.json")


    with open(CONFIG_FILE) as j:
        json_data = json.load(j)

    s3_access_id = json_data["s3Config"]["s3-access-id"]
    s3_access_secret = json_data["s3Config"]["s3-access-secret"]

    #Write credentials in aws cred file
    with open("/root/.aws/credentials", "w") as f:
        f.write("[default]\n")
        f.write("aws_access_key_id = {}\n".format(s3_access_id))
        f.write("aws_secret_access_key = {}".format(s3_access_secret))
 

    if json_data["cloudProvider"] == 'gcp':
        project_id = json_data["gcpConfig"]["projectID"]
        cluster_name = json_data["gcpConfig"]["clusterName"]
        cluster_region = json_data["gcpConfig"]["clusterRegion"]
        availability_zone = json_data["gcpConfig"]["availabilityZone"]
        provider = json_data["cloudProvider"]
        uuid = json_data["gcpConfig"]["uuid"]
        player_rls = json_data["helmCharts"]["player"]["values"]["playerImage"]
        taint_name = json_data["gcpConfig"]["nodeTaintName"]
        pod_type = json_data["gcpConfig"]["podType"]
        helm_repo_uname = json_data["helmCharts"]["player"]["helmLocalRepoUsername"]
        helm_repo_pwd = json_data["helmCharts"]["player"]["helmLocalRepoPassword"]
        helm_chart_version = json_data["helmCharts"]["player"]["helmChartVersion"]

        return project_id,cluster_name,cluster_region,provider,uuid,player_rls,taint_name,pod_type,helm_repo_uname,helm_repo_pwd,helm_chart_version,availability_zone,s3_access_id,s3_access_secret
    else:
        print("Invalid cloud provider : {}".format(json_data["cloudProvider"]))
        sys.exit()

#configures gcp cluster by taking info from configs.json

def configure_cluster(cluster_name,cluster_region,project_id):
    cmnd = "gcloud container clusters get-credentials {0} --region {1} --project {2}".format(cluster_name, cluster_region, project_id)
    p = subprocess.Popen(cmnd, shell=True)
    output, error = p.communicate()

#Get namespace & podname from uuid

def get_namespace(uuid):
    get_ns = uuid+"-ns"
    pod_name = uuid+"-pod"
    return get_ns,pod_name

#Creates namespace

def create_namespace(namespace):
    cmnd = "kubectl create ns {0}".format(namespace)
    p = subprocess.Popen(cmnd, shell=True)
    output,error = p.communicate()

#Access helm repo 

def access_helm_repo(uname,pwd):
    cmnd = "helm repo add local-helm-repo https://serverless-charts.amagi.tv --username {0} --password {1}".format(uname,pwd)
    p = subprocess.Popen(cmnd, shell=True)
    output, error = p.communicate()

# Create pod using helm install command

def create_pod(pod_name,folder_path,namespace,project_id,availability_zone,provider,uuid,player_rls,pod_type,taint_name,helm_chart_version):
    ops_cfg_path = os.path.join(folder_path,"ops_config.ini")   
    cmnd = "helm install {0} local-helm-repo/cp-playout --set-file configPath={1} --set cloudProvider={2} --set uuid={3} --set project={4} --set podType={5} --set availabilityZone={6} --set  playerImage={7}  --set nodeTaintName={8} --set publicOutputProtocol=udp://127.0.0.1:1233 --set podConfig1Key=PLAYER --set serviceDiscoveryRepoRootDirectory=suren --version {9} -n {10}".format(pod_name,ops_cfg_path,provider,uuid,project_id,pod_type,availability_zone,player_rls,taint_name,helm_chart_version,namespace)
    p = subprocess.Popen(cmnd, shell=True)
    output,error = p.communicate()

#Executes deinterlace test script inside pod after checking pod status in pod_start() function

def execute_script(uuid,namespace):
    player_name = "player-"+uuid+"-0"
    cmnd1 = 'kubectl exec -it {0} -n {1} -c player1 -- /bin/bash -c "mkdir ~/.aws; touch ~/.aws/credentials; chmod 777 ~/.aws/credentials; exit"'.format(player_name,namespace)
    cmnd2 = "kubectl cp /root/.aws/credentials {0}/{1}:/root/.aws/credentials -c player1".format(namespace,player_name)
    cmnd3 = 'kubectl exec -it {0} -n {1} -c player1 -- /bin/bash -c "/usr/local/amagi/scripts/deinterlacing_test_framework/test_framework_main.sh 0 4 2 /usr/local/amagi/scripts/deinterlacing_test_framework/template.csv prog"'.format(player_name,namespace)
    p = subprocess.Popen('{};{};{}'.format(cmnd1,cmnd2,cmnd3), shell=True)
    output,error = p.communicate()
    print(output)

#uninstall pod once script execution completes

def delete_pod(pod_name,namespace):
    cmnd = "helm uninstall {0} -n {1}".format(pod_name,namespace)
    p = subprocess.Popen(cmnd, shell=True)
    output,error = p.communicate()

#Check if pod stopped after helm uninstall command

def pod_stop(namespace,pod_name):
    cmnd = "kubectl -n {0} get pods".format(namespace)

    wait_interval = 20
    counter = 0
    while counter <= 10:
        p = subprocess.getoutput(cmnd)
        if "Running" not in p:
            print("Pod has been stopped")
            break
        elif counter == 10:
            print("Pod is still up")
            
        time.sleep(wait_interval)
        counter += 1

#Delete namespace once pod stopped

def delete_namespace(namespace):
    cmnd = "kubectl delete ns {0}".format(namespace)
    p = subprocess.Popen(cmnd, shell=True)
    output,error = p.communicate()

#

def pod_start(namespace,pod_name,uuid):
    cmnd = "kubectl -n {0} get pods".format(namespace)
    wait_interval = 20
    counter = 0
    while counter <= 10:
        p = subprocess.getoutput(cmnd)
        if "Running" in p:
            print("Pod has started and is in running state")
            execute_script(uuid,namespace)
            break
        elif counter == 10:
            print("Pod is not yet up")
        time.sleep(wait_interval)
        counter += 1


def Main():
#    folder_path = sys.argv[1]
#    generateKeyFile(folder_path)
#    project_id,cluster_name,cluster_region,provider,uuid,player_rls,taint_name,pod_type,helm_repo_uname,helm_repo_pwd,helm_chart_version,availability_zone,s3_access_id,s3_access_secret = get_data_from_json(folder_path)
#    configure_cluster(cluster_name,cluster_region,project_id)
#    namespace,pod_name = get_namespace(uuid)
#    access_helm_repo(helm_repo_uname,helm_repo_pwd)
#    delete_pod(pod_name,namespace)
#    delete_namespace(namespace)
#    create_namespace(namespace)
#    create_pod(pod_name,folder_path,namespace,project_id,availability_zone,provider,uuid,player_rls,pod_type,taint_name,helm_chart_version)
#    pod_start(namespace,pod_name,uuid)
#    delete_pod(pod_name,namespace)
#    pod_stop(namespace,pod_name)
#   delete_namespace(namespace)
    print("Hello world from entrypoint script")

Main()
