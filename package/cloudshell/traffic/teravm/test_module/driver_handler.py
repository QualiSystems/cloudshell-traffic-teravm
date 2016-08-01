from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.common import i18n as c
from cloudshell.shell.core.driver_context import AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session

from debug_utils import debugger


class TestModuleHandler:
    def __init__(self):
        pass

    @staticmethod
    def get_inventory(context):
        debugger.attach_debugger()
        api = get_cloudshell_session(context, 'Global')

        vsphere = pyVmomiService(SmartConnect, Disconnect, task_waiter=None)

        resource = api.GetResourceDetails(context.resource.fullname)
        vmuid = resource.VmDetails.UID
        vcenter_name = resource.VmDetails.CloudProviderFullName
        vcenter = api.GetResourceDetails(vcenter_name)
        vcenter_address = vcenter.Address
        vcenter_attr = {attribute.Name:attribute.Value for attribute in vcenter.ResourceAttributes}
        vsphere_user = vcenter_attr[c.ATTRIBUTE_NAME_USER]
        vsphere_password = api.DecryptPassword(vcenter_attr[c.ATTRIBUTE_NAME_PASSWORD]).Value

        si = vsphere.connect(vcenter_address, vsphere_user, vsphere_password)
        vm = vsphere.get_vm_by_uuid(si, vmuid)

        resources = []
        attributes = []
        idx = 1
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                idx += 1
                port_name = 'Comms Interface' if idx == 2 else 'Interface ' + str(idx)
                resources.append(AutoLoadResource(c.TEST_MODULE_PORT_MODEL, port_name, str(idx)))
                attributes.append(AutoLoadAttribute(attribute_name='Requested vNIC Name',
                                                    attribute_value=device.deviceInfo.label,
                                                    relative_address=str(idx)))
        details = AutoLoadDetails(resources, attributes)
        return details
