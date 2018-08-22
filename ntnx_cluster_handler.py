############################################################
#
#  Script: Handle Nutanix Cluster via REST API (v2)
#  Author: Yukiya Shimizu
#  Description: Handle Nutanix Cluster Operation
#  Language: Python3
#
############################################################

import pprint
import json
import requests
import os

V2_BASE_URL = "https://{}:9440/PrismGateway/services/rest/v2.0/"
POST = "post"
GET = "get"
DEBUG = True
NO_CONN = True
DATA_PATH = "./data"
DEBUG_PATH = "./debug"
DISK_TYPE = ["SCSI", "IDE", "PCI"]
pp = pprint.PrettyPrinter(indent=2)


def input_json(fname):
    fpath = os.path.join(DATA_PATH, fname)
    with open(fpath, "rt") as fin:
        return json.load(fin)


def output_json(json_obj, fname):
    fpath = os.path.join(DEBUG_PATH, fname)
    with open(fpath, "wt") as fout:
        json.dump(json_obj, fout, indent=2)


class NtnxRestApiSession:
    def __init__(self, ip_address, username, password):
        self.cluster_ip_address = ip_address
        self.username = username
        self.password = password
        self.v2_url = V2_BASE_URL.format(self.cluster_ip_address)
        self.session = self.get_server_session()

    def get_server_session(self):
        # Creating REST client session for server connection, after globally setting.
        # Authorization, content type, and character set for the session.
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.verify = False
        session.headers.update(
            {'Content-Type': 'application/json; charset=utf-8'})
        return session

    def rest_call(self, method_type, sub_url, payload_json):
        if method_type == GET:
            request_url = self.v2_url + sub_url
            server_response = self.session.get(request_url)
        elif method_type == POST:
            request_url = self.v2_url + sub_url
            server_response = self.session.post(request_url, payload_json)
        else:
            print("method type is wrong!")
            return

        print("Response code: {}".format(server_response.status_code))
        return server_response.status_code, json.loads(server_response.text)


class ClusterModel:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.cluster = {}

        # Sync a specific NTNX cluster information with the target cluster
        print("\nGetting cluster information of the cluster {}".format(self.rest_api.cluster_ip_address))

        if NO_CONN:
            cluster = input_json("cluster.json")
        else:
            rest_status, cluster = self.rest_api.rest_call(GET, "cluster", None)

        if DEBUG:
            output_json(cluster, "cluster.json")

        self.cluster = cluster.copy()

    def get_cluster(self):
        return self.cluster


class ContainerListModel:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.containers = []

        # Sync NTNX containers information with the target cluster
        print("\nGetting containers information of the cluster {}".format(self.rest_api.cluster_ip_address))

        if NO_CONN:
            containers = input_json("containers.json")
        else:
            rest_status, containers = self.rest_api.rest_call(GET, "storage_containers", None)

        if DEBUG:
            output_json(containers, "containers.json")

        self.containers = containers.get("entities").copy()

    def __iter__(self):
        return iter(self.containers)


class NetworkListModel:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.networks = []

        # Sync NTNX networks information with the target cluster
        print("\nGetting networks information of the cluster {}".format(self.rest_api.cluster_ip_address))

        if NO_CONN:
            networks = input_json("networks.json")
        else:
            rest_status, networks = self.rest_api.rest_call(GET, "networks", None)

        if DEBUG:
            output_json(networks, "networks.json")

        self.networks = networks.get("entities").copy()

    def __iter__(self):
        return iter(self.networks)


class VmConfigModel:
    def __init__(self, ntnx_rest_api, vm_name, vm_num_vcpus, vm_num_cores_per_vcpu, vm_memory_mb):
        self.rest_api = ntnx_rest_api
        self.vm_name = vm_name
        self.vm_num_vcpus = vm_num_vcpus
        self.vm_num_cores_per_vcpu = vm_num_cores_per_vcpu
        self.vm_memory_mb = vm_memory_mb
        self.vm_disks = []
        self.vm_nics = []

    def get_vm_name(self):
        return self.vm_name

    def get_vm_num_vcpus(self):
        return self.vm_num_vcpus

    def get_vm_num_cores_per_vcpu(self):
        return self.vm_num_cores_per_vcpu

    def get_vm_memory_mb(self):
        return self.vm_memory_mb

    def get_vm_disks(self):
        return iter(self.vm_disks)

    def get_vm_nics(self):
        return iter(self.vm_nics)

    def add_disk(self, vm_disk_dto):
        self.vm_disks.append(vm_disk_dto)

    def add_nic(self, vm_nic_spec_dto):
        self.vm_nics.append(vm_nic_spec_dto)

    def remove_disk(self):
        pass

    def remove_nic(self):
        pass

    def sync_vm(self):

        vm_config_dto = {"name": self.vm_name, "num_vcpus": self.vm_num_vcpus,
                         "num_cores_per_vcpu": self.vm_num_cores_per_vcpu, "memory_mb": self.vm_memory_mb}

        if self.vm_disks:
            vm_config_dto["vm_disks"] = self.vm_disks

        if self.vm_nics:
            vm_config_dto["vm_nics"] = self.vm_nics

        # Create a NTNX VM on the target cluster
        print("\nCreating a VM on the cluster {}".format(self.rest_api.cluster_ip_address))

        if DEBUG:
            output_json(vm_config_dto, "vm_config_dto.json")

        if not NO_CONN:
            rest_status, vms = self.rest_api.rest_call(POST, "vms", json.dumps(vm_config_dto))

            if vms:
                print("Task Id: {}".format(vms.get("task_uuid")) + "is scheduled")


class ClusterController:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.cluster = None

    def print_cluster(self):
        self.cluster = ClusterModel(self.rest_api).get_cluster()

        # Print cluster
        print("Name: {}".format(self.cluster.get("name")))
        print("ID: {}".format(self.cluster.get("id")))
        print("Cluster External IP Address: {}".format(self.cluster.get("cluster_external_ipaddress")))
        print("Number of Nodes: {}".format(self.cluster.get("num_nodes")))
        print("Version: {}".format(self.cluster.get("version")))
        print("Hypervisor Types: {}".format(self.cluster.get("hypervisor_types")))


class ContainerListController:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.containers = None

    def list_containers(self):
        self.containers = ContainerListModel(self.rest_api)

        # Print containers list
        for i, container in enumerate(self.containers):
            print("Container #{}".format(i) + ":")
            print("\tContainerUuid: {}".format(container.get("storage_container_uuid")))
            print("\tName: {}".format(container.get("name")))
            print("\tCapacity: {}".format(container.get("max_capacity")))

    def print_container(self, container_uuid):
        # Print a specific container information
        pass


class NetworkListController:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.networks = None

    def list_networks(self):
        self.networks = NetworkListModel(self.rest_api)

        # Print networks list
        for i, network in enumerate(self.networks):
            print("Network #{}".format(i) + ":")
            print("\tVLAN ID: {}".format(network.get("vlan_id")))
            print("\tName: {}".format(network.get("name")))
            print("\tNetworkUuid: {}".format(network.get("uuid")))

    def print_network(self, vlan_id):
        # Print a specific network(VLAN) information
        pass


class VmCreationController:
    def __init__(self, ntnx_rest_api):
        self.rest_api = ntnx_rest_api
        self.vm_config_dto = None
        self.containers = None
        self.networks = None

    def create_vm(self):
        print("#" * 79)
        print("NTNX Cluster VM Creation Menu")
        print("#" * 79)

        self.set_vm_required()

        while True:
            print("Please add DISKs to the VM")
            response = input("Do you add DISKs? [Y/N]:")

            if response == "Y":
                print("Y")
                self.add_vm_disk()
                continue
            else:
                break

        while True:
            print("Please add NICs to the VM")
            response = input("Do you add NICs? [Y/N]:")

            if response == "Y":
                print("Y")
                self.add_vm_nic()
                continue
            else:
                break

        if self.confirm_vm_creation():
            self.vm_config_dto.sync_vm()
        else:
            print("The VM is not created!")

    def confirm_vm_creation(self):
        print("#" * 79)
        print("VM Name:" + self.vm_config_dto.get_vm_name())
        print("Number of vCPUs:" + str(self.vm_config_dto.get_vm_num_vcpus()))
        print("Number of cores per vCPU:" + str(self.vm_config_dto.get_vm_num_cores_per_vcpu()))
        print("Memory Size(MB):" + str(self.vm_config_dto.get_vm_memory_mb()))

        print("Disk Information")
        for i, vm_disk in enumerate(self.vm_config_dto.get_vm_disks()):
            print("\tDisk #{}".format(i) + ":")
            for key in vm_disk.keys():
                print("\t\t" + str(key) + ":" + str(vm_disk.get(key)))

        print("Network Information")
        for i, vm_nic in enumerate(self.vm_config_dto.get_vm_nics()):
            print("\tNetwork #{}".format(i) + ":")
            for key in vm_nic.keys():
                print("\t\t" + str(key) + ":" + str(vm_nic.get(key)))

        response = input("Is it OK? [Y/N]:")
        if response == "Y":
            print("Y")
            return True
        else:
            print("N")
            return False

    def set_vm_required(self):
        while True:
            vm_name = input("Please enter a VM Name:")
            vm_num_vcpus = int(input("Please enter number of vCPUs for " + vm_name + ":"))
            vm_num_cores_per_vcpu = int(input("Please enter number of cores per vCPU:"))
            vm_memory_mb = int(input("Please enter memory(mb) for " + vm_name + ":"))

            print("VM Name:" + vm_name)
            print("Number of vCPUs:" + str(vm_num_vcpus))
            print("Number of cores per vCPU:" + str(vm_num_cores_per_vcpu))
            print("Memory Size(MB):" + str(vm_memory_mb))

            response = input("Is it OK? [Y/N]:")
            if response == "Y":
                print("Y")
                break
            else:
                continue

        self.vm_config_dto = VmConfigModel(self.rest_api, vm_name, vm_num_vcpus, vm_num_cores_per_vcpu, vm_memory_mb)

    def add_vm_disk(self):
        vm_disk_dto = {}
        vm_disk_address_dto = {}
        vm_disk_create_dto = {}
        self.containers = ContainerListModel(self.rest_api)

        while True:
            vm_disk_address_dto["device_bus"] = input("Please enter Disk type [SCSI/IDE/PCI]:")
            if vm_disk_address_dto["device_bus"] not in DISK_TYPE:
                print("Please input [SCSI/IDE/PCI]")
                continue

            if vm_disk_address_dto["device_bus"] == "IDE":
                vm_disk_dto["is_cdrom"] = True
                vm_disk_dto["is_empty"] = True
            else:
                vm_disk_dto["is_cdrom"] = False
                vm_disk_dto["is_empty"] = False

            vm_disk_dto["is_scsi_pass_through"] = False

            print("Device Bus:" + vm_disk_address_dto["device_bus"])
            response = input("Is it OK? [Y/N]:")

            if response == "Y":
                break
            else:
                continue

        # Make user to select ContainerUuid from the list of Container
        while True:
            if vm_disk_address_dto["device_bus"] == "IDE":
                break
            else:
                print("Select a container from following containers' list")
                print("#" * 79)
                containers_dict = {}

                for container in self.containers:
                    containers_dict[container["name"]] = container

                for container_name in containers_dict.keys():
                    print(container_name)

                container_name = input("Please enter a Container Name for placing the VM:")
                disk_size = input("Please enter the size(GB) of disk:")
                container_confirm = input(container_name + " (" + disk_size + " GB)? [Y/N]:")
                if container_confirm == "Y":
                    print(container_name + " is selected")
                    vm_disk_create_dto["storage_container_uuid"] = \
                        containers_dict[container_name].get("storage_container_uuid")
                    vm_disk_create_dto["size"] = int(disk_size) * 1024 * 1024 * 1024
                    break
                else:
                    continue

        vm_disk_dto["disk_address"] = vm_disk_address_dto

        if vm_disk_address_dto["device_bus"] != "IDE":
            vm_disk_dto["vm_disk_create"] = vm_disk_create_dto

        if vm_disk_dto:
            self.vm_config_dto.add_disk(vm_disk_dto)

    def add_vm_nic(self):
        vm_nic_spec_dto = {}
        self.networks = NetworkListModel(self.rest_api)

        # Make user to select NetworkUuid from the list of Network
        while True:
            print("Select a network from following networks' list")
            print("#" * 79)
            networks_dict = {}

            for network in self.networks:
                networks_dict[network["name"]] = network

            for network_name in networks_dict.keys():
                display_net_address = str(networks_dict[network_name].get("ip_config").get("network_address"))
                print(network_name + ":" + display_net_address)

            network_name = input("Please enter a Network Name for placing VM:")
            network_confirm = input(network_name + "? [Y/N]:")
            if network_confirm == "Y":
                if network_name in networks_dict:
                    print(network_name + " is selected")
                    vm_nic_spec_dto["uuid"] = networks_dict[network_name].get("uuid")
                    break
                else:
                    print(network_name + " is not right!!!")
                    continue
            else:
                continue

        while True:
            vm_nic_spec_dto["request_ip"] = False
            network_confirm = input("Do you want to request IP address?[Y/N]:")
            if network_confirm == "Y":
                request_ip_address = input("Please enter request IP address(xxx.xxx.xxx.xxx):")
                ip_address_confirm = input("IP Address: " + request_ip_address + "\nIs it OK? [Y/N]:")
                if ip_address_confirm == "Y":
                    vm_nic_spec_dto["requested_ip_address"] = request_ip_address
                    vm_nic_spec_dto["request_ip"] = True
                    break
                else:
                    continue
            else:
                break

        if vm_nic_spec_dto:
            self.vm_config_dto.add_nic(vm_nic_spec_dto)


class MainMenu:
    def __init__(self):
        print("Welcome to NTNX Cluster Handler Menu")
        tgt_cluster_ip = input("Please enter the Cluster Virtual IP Address\n")
        tgt_username = input("Please enter username for the cluster\n")
        tgt_password = input("Please enter password for the username\n")
        print("#" * 79)
        print("Cluster IP Address: " + tgt_cluster_ip)
        print("Cluster username/password: " + tgt_username + "/" + ("*" * len(tgt_password)) + "\n")

        self.rest_api = NtnxRestApiSession(tgt_cluster_ip, tgt_username, tgt_password)

    def main_loop(self):
        try:
            while True:
                print("#" * 79)
                print("NTNX Cluster Handler Main Menu")
                print("1:  Show Cluster Information")
                print("2:  List Storage Containers")
                print("3:  List Networks")
                print("4:  List VMs")
                print("5:  Create a VM")
                print("99: Exit Menu")
                print("#" * 79)
                response = input("Please enter cluster operation\n")

                if response == "99":
                    print("NTNX Cluster Handler Exit")
                    break
                elif response == "1":
                    ClusterController(self.rest_api).print_cluster()
                    continue
                elif response == "2":
                    ContainerListController(self.rest_api).list_containers()
                    continue
                elif response == "3":
                    NetworkListController(self.rest_api).list_networks()
                    continue
                elif response == "4":
                    print("Not Implemented!")
                    continue
                elif response == "5":
                    VmCreationController(self.rest_api).create_vm()
                    continue
                else:
                    print("Wrong Operation: " + response)
                    continue

        except Exception as ex:
            print(ex)
            exit(1)

if __name__ == "__main__":
    MainMenu().main_loop()
