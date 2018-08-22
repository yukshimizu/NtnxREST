# NtnxREST
Example usages of Nutanix REST API

ntnx_cluster_handler.py shows follwoing menu and handles those operations via v2 API.

1. Show Cluster Information
2. List Storage Containers
3. List Networks
4. List VMs
5. Crate a VM

When DEBUG in the script is True, the script outputs return body from REST API with json format at the path defined as DEBUG_PATH.
When NO_CONN in the script is True, the script uses json input as return body.
