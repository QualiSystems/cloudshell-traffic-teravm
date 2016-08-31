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
        logical_names_for_load = TestModuleHandler.get_logical_names_for_load_configuration(resource.VmDetails.VmCustomParams)
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
                attributes.append(AutoLoadAttribute(attribute_name=c.ATTRIBUTE_NAME_LOGICAL_NAME,
                                                    attribute_value=logical_names_for_load.get(port_name, ''),
                                                    relative_address=str(idx)))
        api.UpdateResourceAddress(resource.Name, address)
        api.SetResourceLiveStatus(resource.Name, 'Online', 'Active')
        details = AutoLoadDetails(resources, attributes)
        return details

    @staticmethod
    def get_logical_names_for_load_configuration(vm_params_list):
        """
        :param vm_params_list: [cloudshell.api.cloudshell_api.VmCustomParam]
        :rtype: dict
        """
        # port1:logicaleelementname1;port2:logicaleelementname2;port3:logicaleelementname3

        logical_names_raw = (param.Value for param in vm_params_list if param.Name == c.KEY_PORTS_LOGICAL_NAMES).next()
        logical_names_dict = dict()
        if ':' in logical_names_raw:
            port_pairs = logical_names_raw.split(';')
            for port_pair in port_pairs:
                port_pair = port_pair.split(':')
                try:
                    logical_names_dict[port_pair[0]] = port_pair[1]
                except IndexError:
                    continue
        return logical_names_dict

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

        connectors = context.connectors
        if not connectors:
            return 'Success'

        debugger.attach_debugger()

        ports = TestModuleHandler._get_test_ports(resource)

        to_disconnect = []
        to_add = []

        for connector in connectors:
            source, me, other = TestModuleHandler._set_remap_connector_details(connector, resource_name)
            to_disconnect.extend([me, other])

        # these are connectors from app to vlan where user marked to which interface the connector should be connected
        connectors_with_predefined_target = [connector for connector in connectors if connector.source != '']

        # these are connectors from app to vlan where user left the target interface unspecified
        connectors_without_target = [connector for connector in connectors if connector.source == '']

        for connector in connectors_with_predefined_target:
            if connector.source not in ports.keys():
                raise Exception('Tried to connect an interface that is not on reservation - ', connector.source)

            else:
                if hasattr(ports[connector.source], 'allocated'):
                    raise Exception('Tried to connect several connections to same interface: ', connector.source)

                else:
                    to_add.append(SetConnectorRequest(SourceResourceFullName=ports[connector.source].Name,
                                                      TargetResourceFullName=connector.other,
                                                      Direction=connector.direction,
                                                      Alias=connector.alias))
                    ports[connector.source].allocated = True

        unallocated_ports = [port for key, port in ports.items() if not hasattr(port, 'allocated')]

        if len(unallocated_ports) < len(connectors_without_target):
            raise Exception('There were more connections to TeraVM than available interfaces after deployment.')
        else:
            for port in unallocated_ports:
                connector = connectors_without_target.pop()
                to_add.append(SetConnectorRequest(SourceResourceFullName=port.Name,
                                                  TargetResourceFullName=connector.other,
                                                  Direction=connector.direction,
                                                  Alias=connector.alias))

        if connectors_without_target:
            raise Exception('There were more connections to TeraVM than available interfaces after deployment.')

        api.RemoveConnectorsFromReservation(reservation_id, to_disconnect)
        api.SetConnectorsInReservation(reservation_id, to_add)

        return 'Success'

    @staticmethod
    def _set_remap_connector_details(connector, resource_name):
        attribs = connector.attributes
        if resource_name in connector.source.split('/'):
            source = attribs.get(c.ATTRIBUTE_REQUESTED_SOURCE_VNIC_NAME, '')
            me = connector.source
            other = connector.target

        elif resource_name in connector.target.split('/'):
            source = attribs.get(c.ATTRIBUTE_REQUESTED_SOURCE_VNIC_NAME, '')
            me = connector.target
            other = connector.source

        else:
            raise Exception("Oops, a connector doesn't have required details:\n Connector source: {0}\n"
                            "Connector target: {1}\nPlease contact your admin".format(connector.source,
                                                                                      connector.target))

        connector.source = source
        connector.me = me
        connector.other = other

        return source, me, other

    @staticmethod
    def _get_test_ports(resource):
        ports = {port.Name.split('/')[-1]: port for port in resource.ChildResources
                 if port.ResourceModelName == c.TEST_MODULE_PORT_MODEL and
                 c.COMMS_INTERFACE not in port.Name}
        return ports
