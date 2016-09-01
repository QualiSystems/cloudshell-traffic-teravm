import requests
import json


def get_interface_tvm_resource_ids(macs, pool_manager_ip):
    """
    :type macs: list(str)
    :type pool_manager_ip: str
    :rtype: list(str)
    """

    response = requests.get(url=str.format('http://{0}:8080/poolmanager/api/testModules', pool_manager_ip),
                            headers={"Accept": "application/vnd.cobham.v1+json"})
    test_modules_in_pool = json.loads(response.text)
    tvm_resource_ids = [resource['resourceId'] for resource in test_modules_in_pool['testModules']
                        if resource['macAddress'] in macs]
    return tvm_resource_ids


def reserve_interfaces_in_pool_manager(tvm_resource_ids, reservation_owner, pool_manager_ip):
    ro = reservation_owner.replace(' ', '_')  # tvm users can't have spaces in there names!
    reserve_test_module_data = {'reserveFor': ro, 'targetTestModuleIds': tvm_resource_ids}
    result = requests.put(url=str.format('http://{0}:8080/poolmanager/api/testModules/reserve', pool_manager_ip),
                          headers={"Accept": "application/vnd.cobham.v1+json",
                          "Content-Type": "application/vnd.cobham.v1+json"},
                          json=reserve_test_module_data)
    print result


def unreserve_interfaces_in_pool_manager(tvm_resource_ids, pool_manager_ip):
    reserve_test_module_data = {'targetTestModuleIds': tvm_resource_ids}
    result = requests.put(url=str.format('http://{0}:8080/poolmanager/api/testModules/reserve', pool_manager_ip),
                          headers={"Accept": "application/vnd.cobham.v1+json",
                          "Content-Type": "application/vnd.cobham.v1+json"},
                          json=reserve_test_module_data)
    print result


def unregister_interfaces_in_pool_manager(tvm_resource_ids, pool_manager_ip):
    for resource_id in tvm_resource_ids:
        result = requests.delete(url=str.format('http://{0}:8080/poolmanager/api/testModules/{1}',
                                                pool_manager_ip,
                                                resource_id),
                                 headers={"Accept": "application/vnd.cobham.v1+json",
                                          "Content-Type": "application/vnd.cobham.v1+json"})
        print result
