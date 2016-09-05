from cloudshell.traffic.teravm.common import i18n as c
from cloudshell.traffic.teravm.controller.teravm_executive_helper import get_interface_tvm_resource_ids, \
    unregister_interfaces_in_pool_manager
import re
from debug_utils import debugger


def cleanup(vm_resource):
    """
    :type vm_resource: cloudshell.shell.core.driver_context.ResourceContextDetails
    :return:
    """
    tvm_e_address = vm_resource.attributes[c.ATTRIBUTE_NAME_TVM_EXECUTIVE]

    try:
        if vm_resource.model == c.TEST_MODULE_MODEL \
                and _is_mac(vm_resource.address) \
                and _is_ip(tvm_e_address):
            resource_ids = get_interface_tvm_resource_ids([vm_resource.address], tvm_e_address)
            unregister_interfaces_in_pool_manager(resource_ids, tvm_e_address)
        return ''
    except ValueError:
        raise Exception('No response from TeraVM Executive at {0}. \nCould not unregister {1} '
                        'with mac {2}'.format(tvm_e_address, c.TEST_MODULE_MODEL, vm_resource.address))


def _is_mac(candidate):
    return re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", candidate.lower())


def _is_ip(candidate):
    pieces = candidate.split('.')
    if len(pieces) != 4:
        return False
    try:
        return all(0 <= int(p) < 256 for p in pieces)
    except ValueError:
        return False
