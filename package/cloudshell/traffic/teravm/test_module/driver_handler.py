from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.common import i18n as c
from cloudshell.shell.core.driver_context import AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.api.cloudshell_api import SetConnectorRequest
from cloudshell.traffic.teravm.common.parsing_utilities import to_int_or_maxint
from cloudshell.traffic.teravm.common.vsphere_helper import get_vsphere_credentials
from debug_utils import debugger


class TestModuleHandler:
    def __init__(self):
        pass

    @staticmethod
    def get_inventory(context):
        api = get_cloudshell_session(context, 'Global')

        resource = api.GetResourceDetails(context.resource.fullname)
        vmuid = resource.VmDetails.UID
        vcenter_address, vsphere_password, vsphere_user = get_vsphere_credentials(api, resource)
        vsphere = pyVmomiService(SmartConnect, Disconnect, task_waiter=None)
        si = vsphere.connect(vcenter_address, vsphere_user, vsphere_password)
        vm = vsphere.get_vm_by_uuid(si, vmuid)

        resources = []
        attributes = []
        address = ''
        idx = 1
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                idx += 1
                port_name = c.COMMS_INTERFACE if idx == 2 else c.INTERFACE + str(idx)
                if idx == 2:
                    address = device.macAddress
                resources.append(AutoLoadResource(c.TEST_MODULE_PORT_MODEL, port_name, str(idx)))
                attributes.append(AutoLoadAttribute(attribute_name=c.ATTRIBUTE_REQUESTED_VNIC_NAME,
                                                    attribute_value=device.deviceInfo.label,
                                                    relative_address=str(idx)))
        api.UpdateResourceAddress(resource.Name, address)
        api.SetResourceLiveStatus(resource.Name, 'Online', 'Active')
        details = AutoLoadDetails(resources, attributes)
        return details

    @staticmethod
    def destroy_vm_only(self, context, ports):
        # release starting_index which means I need to have it first
        # call_remote_connected
        debugger.attach_debugger()
        pass

    @staticmethod
    def connect_child_resources(context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :rtype: str
        """
        api = get_cloudshell_session(context, 'Global')
        resource_name = context.resource.fullname
        reservation_id = context.reservation.reservation_id
        resource = api.GetResourceDetails(resource_name)

        ports = TestModuleHandler._get_test_ports(resource)
        connectors = context.connectors
        to_disconnect = []
        to_add = []

        for connector in connectors:
            interface, me, other = TestModuleHandler._set_remap_connector_details(connector, resource_name)
            to_disconnect.extend([me, other])

        connectors.sort(key=lambda x: x.sequence)
        ports.sort()

        for port in ports:
            connector = connectors.pop()
            to_add.append(SetConnectorRequest(SourceResourceFullName=port,
                                              TargetResourceFullName=connector.other,
                                              Direction=connector.direction,
                                              Alias=connector.alias))

        if connectors:
            raise Exception('There were more connections to TeraVM than available interfaces after deployment.')

        api.RemoveConnectorsFromReservation(reservation_id, to_disconnect)
        api.SetConnectorsInReservation(reservation_id, to_add)

        return 'Success'

    @staticmethod
    def _set_remap_connector_details(connector, resource_name):
        attribs = connector.attributes
        if resource_name in connector.source.split('/'):
            sequence = to_int_or_maxint(attribs.get(c.ATTRIBUTE_SEQUENCE, ''))
            me = connector.source
            other = connector.target

        elif resource_name in connector.target.split('/'):
            sequence = to_int_or_maxint(attribs.get(c.ATTRIBUTE_SEQUENCE, ''))
            me = connector.target
            other = connector.source

        else:
            raise Exception("Oops, a connector doesn't have required details:\n Connector source: {0}\n"
                            "Connector target: {1}\nPlease contact your admin".format(connector.source,
                                                                                      connector.target))

        connector.sequence = sequence
        connector.me = me
        connector.other = other

        return sequence, me, other

    @staticmethod
    def _get_test_ports(resource):
        ports = [port.Name for port in resource.ChildResources if port.ResourceModelName == c.TEST_MODULE_PORT_MODEL and
                 c.COMMS_INTERFACE not in port.Name]
        return ports
