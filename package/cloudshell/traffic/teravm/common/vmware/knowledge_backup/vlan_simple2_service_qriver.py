import random
from qualipy.virtualization.vcenter.vcenter_dropdown_manager import vlan_numbers_from_network_dropdown_value, \
    vlan_mode_from_network_dropdown_value

__author__ = 'ericr'
import json
from qualipy.api.cloudshell_api_enhanced import CloudShellAPIEnhancedSession
from qualipy.virtualization.vcenter import vcenter_i18n
from qualipy.common.libs.driver_builder_wrapper import BaseServiceDriver, DriverFunction


def is_change(status):
    return status.startswith('connected:') or status.startswith('disconnected:')


class VlanSimple2ServiceDriver(BaseServiceDriver):
    @DriverFunction
    def Init(self, matrix_json):
        BaseServiceDriver.Init(self, matrix_json)
        m = json.loads(matrix_json)
        self.testshell_ip = m['connectivityInfo']['ServerAddress']
        self.testshell = None
        self.connectivityinfo = m['connectivityInfo']

    def ensure_testshell(self, matrix_json):
        m = json.loads(matrix_json)
        if self.testshell is None:
            testshell_user = m['reservation'][vcenter_i18n.TESTSHELL_USERNAME_ATTR]
            testshell_password = m['reservation'][vcenter_i18n.TESTSHELL_PASSWORD_ATTR]
            testshell_domain = m['reservation'][vcenter_i18n.TESTSHELL_DOMAIN_ATTR]
            self.testshell = CloudShellAPIEnhancedSession(self.testshell_ip,
                                                         testshell_user, testshell_password, testshell_domain)
        self.resid = m['reservation']['ReservationId']
        self.domain = m['reservation']['Domain']
        self.service_name = m['resource']['ResourceName']

    @DriverFunction(alias="Connect All")
    def connect_all(self, matrix_json):
        self.ensure_testshell(matrix_json)

        service_attrs = self.testshell.get_service_attributes(self.resid, self.service_name)

        def is_vlan_target(p):
            root = self.testshell.get_root_resource(p)
            attrs = self.testshell.get_resource_attributes(root)

            # skip L1 for free before doing expensive queries
            if 'l1' in attrs['family'].lower() or 'patch' in attrs['family'].lower():
                return False

            # L2
            if 'L2 Switch Type' in attrs:
                return True

            # VM
            if attrs['family'] == vcenter_i18n.ROOT_VM_FAMILY:
                return True

            # logical VM
            for conn in attrs.connections:
                root2 = self.testshell.get_root_resource(conn)
                attrs2 = self.testshell.get_resource_attributes(root2)
                if attrs2['family'] == vcenter_i18n.ROOT_VM_FAMILY:
                    return True

            return False

        def is_l1_switch(x):
            attrs = self.testshell.get_resource_attributes(x)
            return 'l1' in attrs['family'].lower() or 'patch' in attrs['family'].lower()

        port2target_isdirects = {}
        for port in self.testshell.get_service_connections(self.resid, self.service_name):
            port, root = self.testshell.get_resource_name_and_root(port)

            target_isdirects = self.testshell.find_target_ports(port,
                                                                is_eligible_target_port=is_vlan_target,
                                                                is_eligible_for_traversal=is_l1_switch)
            port2target_isdirects[port] = target_isdirects
            self.testshell.filter_resources_by_availability(self.resid, [a[0] for a in target_isdirects])


        port2target_isdirect = {}
        for i in range(0, 100):
            port2target_isdirect = {}
            usedtargets = set()
            for port in port2target_isdirects:
                for j in range(0, 100):
                    target_isdirect = random.choice(port2target_isdirects[port])
                    if target_isdirect not in usedtargets:
                        port2target_isdirect[port] = target_isdirect
                        usedtargets.add(target_isdirect)
                        break
                if port not in port2target_isdirect:
                    break
            if len(port2target_isdirect) == len(port2target_isdirects):
                break

        print port2target_isdirects

        if len(port2target_isdirect) < len(port2target_isdirects):
            raise Exception('Failed to assign a unique reachable L2 port to each connected DUT. Candidates: {0}'.format(port2target_isdirects))

        for port, target_isdirect in port2target_isdirects.iteritems():
            target = target_isdirect[0]
            is_direct = target_isdirect[1]
            if not is_direct:
                self.testshell.CreateRouteInReservation(reservationId=self.resid,
                                                        sourceResourceFullPath=port,
                                                        targetResourceFullPath=target_isdirect,
                                                        overrideActiveRoutes=True,
                                                        mappingType='bi',
                                                        maxHops=6,
                                                        isShared=False,
                                                        routeAlias=self.service_name)
                self.testshell.ConnectRoutesInReservation(reservationId=self.resid,
                                                          endpoints=[port, target],
                                                          mappingType='bi')

            # todo check success


            target_root = self.testshell.get_connected_root_resource(target)
            target_root_attrs = self.testshell.get_resource_attributes(target_root)

            vmtarget = None
            if target_root_attrs['family'] == vcenter_i18n.ROOT_VM_FAMILY:
                vmtarget = target_root
            else:
                target2_root = self.testshell.get_connected_root_resource(target_root)
                if target2_root is not None:
                    target2_root_attrs = self.testshell.get_resource_attributes(target2_root)
                    if target2_root_attrs['family'] == vcenter_i18n.ROOT_VM_FAMILY:
                        vmtarget = target2_root

            if vmtarget is not None:
                self.testshell.AddResourcesToReservation(self.resid, [vmtarget], shared=False)
                self.testshell.ExecuteResourceCommand(self.resid, vmtarget, 'connect', [self.service_name], printOutput=True)
            else:
                vlan_id = vlan_numbers_from_network_dropdown_value(service_attrs[vcenter_i18n.NETWORK_ATTR])
                vlan_mode = vlan_mode_from_network_dropdown_value(service_attrs[vcenter_i18n.NETWORK_ATTR])
                self.testshell.AddResourcesToReservation(self.resid, [target_root, target], shared=False)
                self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                               target_root,
                                                               'Add_VLAN',
                                                               'VLAN',
                                                               [vlan_id, vlan_mode, ''],
                                                               [target],
                                                               printOutput=True)



if __name__ == '__main__':
    j = '''{
        "resource": {
            "ResourceName" : "vlan335",
            "VLAN ID" : "335",
            "Mode" : "Access"

        },
        "reservation": {
            "ReservationId": "ef7b220b-4d76-43b8-ad95-e09ed737cdac",
            "Username": "admin",
            "Password": "admin",
            "AdminUsername": "admin",
            "AdminPassword": "admin",
            "Domain": "Global"
        },
        "connectivityInfo": {
            "ServerAddress": "localhost"
        }
    }'''
    driver = VlanSimple2ServiceDriver('aoeuaeouaeu',  j)
    driver.connect_all(j)