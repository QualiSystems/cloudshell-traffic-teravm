import json
from qualipy.api.cloudshell_api_enhanced import CloudShellAPIEnhancedSession
from qualipy.virtualization.vcenter import vcenter_i18n
from qualipy.common.libs.driver_builder_wrapper import BaseServiceDriver, DriverFunction

__author__ = 'ericr'


def is_change(status):
    return status.startswith('connected:') or status.startswith('disconnected:')


class VlanSimpleServiceDriver(BaseServiceDriver):
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

    @DriverFunction
    def create(self, matrix_json):
        self.ensure_testshell(matrix_json)

        attrs = self.testshell.get_service_attributes(self.resid, self.service_name)

    @DriverFunction
    def connect_all(self, matrix_json):
        return self.connect_or_disconnect_all(matrix_json, True)

    @DriverFunction
    def disconnect_all(self, matrix_json):
        return self.connect_or_disconnect_all(matrix_json, False)

    def connect_or_disconnect_all(self, matrix_json, is_connect):
        self.ensure_testshell(matrix_json)

        updates = 0
        messages = []

        i = 1
        steadystate = False
        while not steadystate:
            steadystate = True
            m = 'Pass #{0}:'.format(i)
            self.testshell.write_message(self.resid, m)
            messages.append(m)
            for conn in self.testshell.get_service_connections(self.resid, self.service_name):
                if is_connect:
                    v = self.add_connector(matrix_json, conn)
                else:
                    v = self.remove_connector(matrix_json, conn)
                if is_change(v):
                    steadystate = False
                    updates += 1
                self.testshell.write_message(self.resid, v)
                messages.append(v)
            i += 1

        return 'Performed {0} updates: {1}'.format(updates, messages)

    @DriverFunction
    def add_connector(self, matrix_json, dut):
        return self.add_or_remove_connector(matrix_json, dut, True)

    @DriverFunction
    def remove_connector(self, matrix_json, dut):
        return self.add_or_remove_connector(matrix_json, dut, False)

    def add_or_remove_connector(self, matrix_json, dut, is_add):
        self.ensure_testshell(matrix_json)

        attrs = self.testshell.get_service_attributes(self.resid, self.service_name)
        if is_add:
            connector_alias_to_set = 'VLAN Connected'
            no_action_message = 'already connected'
            action_complete_message = 'connected: {0}'
            command2args = {
                'Add_VLAN': [attrs['VLAN Mode'], attrs['VLAN ID'], attrs['VLAN Addtional Info']],
                'remote_connect': [self.service_name],
            }
        else:
            connector_alias_to_set = ''
            no_action_message = 'already disconnected'
            action_complete_message = 'disconnected: {0}'
            command2args = {
                'Remove_VLAN': [attrs['VLAN Mode'], attrs['VLAN ID'], attrs['VLAN Addtional Info']],
                'remote_disconnect': [self.service_name],
            }

        if self.testshell.get_connector_alias(self.resid, self.service_name, dut) == connector_alias_to_set:
            return no_action_message

        if self.testshell.is_service(self.resid, dut):
            return 'skipping service connector'

        res = self.testshell.try_connected_command(self.resid, dut, command2args)
        if res is None:
            conns = self.testshell.get_service_connections(self.resid, self.service_name)
            for conn in conns:
                if conn != dut and not self.testshell.is_service(self.resid, conn):
                    connport, ignore1 = self.testshell.get_resource_name_and_root(conn)
                    for route in self.testshell.GetRoutesSolution(self.resid, [dut], [connport], 'bi', 100, False).Routes:
                        for seg in route.Segments:
                            if self.testshell.get_root_resource(seg.Source) == self.testshell.get_root_resource(seg.Target):
                                res = self.testshell.try_connected_command(self.resid, seg.Target, command2args)
                                if res is not None:
                                    break
                if res is not None:
                    break

        if res is not None:
            self.testshell.UpdateConnectorAliasInReservation(self.resid, self.service_name, dut, 'bi', connector_alias_to_set)
            return action_complete_message.format(res)

        return 'no route found, try again after adding more DUTs'


