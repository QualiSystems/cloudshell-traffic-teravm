import json
import random
import re
from qualipy.api.cloudshell_api import AttributeNameValue
from qualipy.api.cloudshell_api_enhanced import CloudShellAPIEnhancedSession
from qualipy.virtualization.vcenter import vcenter_i18n
from qualipy.common.libs.driver_builder_wrapper import BaseServiceDriver, DriverFunction

__author__ = 'ericr'


def istrue(param):
    return str(param).lower() in ['true', 'yes', 'on', '1']

VLAN_SERVICE_MODE_ATTR = 'VLAN Mode'
VLAN_SERVICE_VLAN_ID_ATTR = 'VLAN ID'
VLAN_SERVICE_SHARE_VLAN_ATTR = 'Share VLAN'
VLAN_SERVICE_VLAN_RANGE_ATTR = 'VLAN Range'
VLAN_SERVICE_AUTO_ATTR = 'Auto Allocate VLAN'
VLAN_SERVICE_ADDITIONAL_INFO_ATTR = 'VLAN Additional Info'

VLAN_SERVICE_MANAGEMENT_VLAN_ATTR = 'Management VLAN'

class VlanService(BaseServiceDriver):

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

    def validate_endpoint_not_connected_to_vlan_service(self, duts):
        services = set()
        rd = self.testshell.GetReservationDetails(self.resid).ReservationDescription
        for service in rd.Services:
            if service.Alias != self.service_name:
                services.add(service.Alias)
        dutset = set(duts)
        bad = []
        for conn in rd.Connectors:
            if conn.Source in services and conn.Target in dutset:
                bad.append(conn.Target + '<->' + conn.Source)
            if conn.Target in services and conn.Source in dutset:
                bad.append(conn.Source + '<->' + conn.Target)
        if len(bad) > 0:
            raise Exception('Error: {0}: DUTs already connected to another VLAN service: {1}'.format(self.service_name, ', '.join(bad)))

    def remove_vlan(self, matrix_json, duts, from_update_command, remove_service_activated, unlock_resource_in_the_end):
        command_name = 'Remove_VLAN'
        command_tag = 'VLAN'
        self.testshell.write_message(self.resid, 'VLAN service {0}: Start removing'.format(self.service_name))
        is_management_vlan = False

        attrs = self.testshell.get_service_attributes(self.resid, self.service_name)
        service_mode = attrs[VLAN_SERVICE_MODE_ATTR]
        service_vlan_id = attrs[VLAN_SERVICE_VLAN_ID_ATTR]
        service_share_vlan = istrue(attrs[VLAN_SERVICE_SHARE_VLAN_ATTR])
        service_additional_info = attrs[VLAN_SERVICE_ADDITIONAL_INFO_ATTR]
        is_auto = istrue(attrs[VLAN_SERVICE_AUTO_ATTR])
        if VLAN_SERVICE_MANAGEMENT_VLAN_ATTR in attrs:
            is_management_vlan = istrue(attrs[VLAN_SERVICE_MANAGEMENT_VLAN_ATTR])

        rdet = self.testshell.GetReservationDetails(self.resid).ReservationDescription
        duts_on_not_available_vlans = []
        duts_on_available_vlans = []
        duts_on_all_vlans = []
        for conn in rdet.Connectors:
            x = None
            if conn.Source == self.service_name:
                x = conn.Target
            if conn.Target == self.service_name:
                x = conn.Source
            if x is not None:
                duts_on_all_vlans.append(x)
                if conn.Alias == 'N/A VLAN':
                    duts_on_not_available_vlans.append(x)
                if conn.Alias == 'VLAN Created':
                    duts_on_available_vlans.append(x)

        if service_vlan_id == '':
            if VLAN_SERVICE_VLAN_RANGE_ATTR in attrs:
                service_vlan_id = attrs[VLAN_SERVICE_VLAN_RANGE_ATTR]
            else:
                service_vlan_id = '-1'

        vlans = self.get_all_vlans_from_vlan_id_input(service_vlan_id)
        if unlock_resource_in_the_end:
            self.testshell.UnlockResources(self.resid, duts)

        errors = []
        removed_duts = []
        l1_duts = []
        for dut in duts:
            try:
                self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                               self.testshell.get_root_resource(dut),
                                                               command_name,
                                                               command_tag,
                                                               [service_mode, service_vlan_id, service_additional_info],
                                                               [dut],
                                                               printOutput=True)
                removed_duts.append(dut)
            except:
                if self.is_resource_connected_to_l1(dut):
                    l1_duts.append(dut)
                else:
                    errors.append('VLAN service {0}: DUT {1} not connected to L1 or L2'.format(self.service_name, dut))

        duts_on_available_vlans += removed_duts

        if len(l1_duts) > 0:
            if len(duts_on_available_vlans) > 0:
                for dut in l1_duts:
                    is_found_l2, found_switch = self.configure_route_for_dut_remove(dut, duts_on_available_vlans[0])
                    for dut2 in duts_on_available_vlans:
                        if dut != dut2:
                            is_found_l2, found_switch = self.configure_route_for_dut_remove(dut, dut2)
                            if is_found_l2:
                                break
                    if is_found_l2:
                        connfp = self.testshell.get_connected_resource(found_switch)
                        child, root = self.testshell.get_resource_name_and_root(connfp)
                        self.testshell.AddResourcesToReservation(self.resid, [child, root], shared=False)
                        self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                                       root,
                                                                       command_name,
                                                                       command_tag,
                                                                       [service_mode, service_vlan_id, service_additional_info],
                                                                       [child],
                                                                       printOutput=True)

                    else:
                        raise Exception('VLAN service {0}: Could not find connected L2 for DUT {1}'.format(self.service_name, dut))

            else:
                if len(l1_duts) > 1:
                    dut_to_config_with = l1_duts[0]
                    is_found_l2 = False
                    for dut in l1_duts:
                        if dut != dut_to_config_with:
                            is_found_l2, found_switch = self.configure_route_for_dut_remove(dut, dut_to_config_with)
                            if is_found_l2:
                                connfp = self.testshell.get_connected_resource(found_switch)
                                child, root = self.testshell.get_resource_name_and_root(connfp)
                                self.testshell.AddResourcesToReservation(self.resid, [child, root], shared=False)
                                self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                                               root,
                                                                               command_name,
                                                                               command_tag,
                                                                               [service_mode, service_vlan_id, service_additional_info],
                                                                               [child],
                                                                               printOutput=True)
                    dut_to_config_with = l1_duts[1]
                    if len(duts_on_not_available_vlans) > 0:
                        is_found_l2, found_switch = self.configure_route_for_dut_remove(l1_duts[0], dut_to_config_with)
                        if is_found_l2:
                            connfp = self.testshell.get_connected_resource(found_switch)
                            child, root = self.testshell.get_resource_name_and_root(connfp)
                            self.testshell.AddResourcesToReservation(self.resid, [child, root], shared=False)
                            self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                                           root,
                                                                           command_name,
                                                                           command_tag,
                                                                           [service_mode, service_vlan_id, service_additional_info],
                                                                           [child],
                                                                           printOutput=True)
            duts_not_removed = []
            if len(duts_on_available_vlans) > 0:
                all_available_unremoved = set(duts_on_available_vlans)
                all_available_unremoved.difference_update(duts)
                duts_not_removed = list(all_available_unremoved)
            else:
                duts_not_removed = []

            if len(duts_not_removed) == 1:
                if self.is_resource_connected_to_l1(duts_not_removed[0]):
                    is_found_l2, i1, connected_to_l1_name, i3 = self.get_connected_l2_and_unmap_l1s(duts_not_removed[0])
                    if is_found_l2:
                        l1child, l1root = self.testshell.get_resource_name_and_root(connected_to_l1_name)
                        self.testshell.AddResourcesToReservation(self.resid, [l1root], shared=True)
                        self.testshell.write_message(self.resid, 'VLAN service {0}: Removing VLAN from DUT That connected to L1'.format(self.service_name))
                        self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                                       l1root,
                                                                       command_name,
                                                                       command_tag,
                                                                       [service_mode, service_vlan_id, service_additional_info],
                                                                       [l1child],
                                                                       printOutput=True)
                        self.testshell.UpdateConnectorAliasInReservation(self.resid, self.service_name, duts_not_removed[0], 'bi', 'N/A VLAN')
            # if not is_management_vlan:
            #     if (len(connectors_by_source) == 1 and len(connectors_by_target) == 0) or from_update_command or remove_service_activated:
            #         pass




    def create_vlan(self, matrix_json, duts, update_vlan_id, update_vlan_share, is_updating):

        self.ensure_testshell(matrix_json)

        add_vlan_command_name = 'Add_VLAN'
        vlan_command_tag = 'VLAN'
        error_occurred = False
        is_management_vlan = False

        attrs = self.testshell.get_service_attributes(self.resid, self.service_name)
        service_mode = attrs[VLAN_SERVICE_MODE_ATTR]
        service_vlan_id = attrs[VLAN_SERVICE_VLAN_ID_ATTR]
        service_share_vlan = istrue(attrs[VLAN_SERVICE_SHARE_VLAN_ATTR])
        service_additional_info = attrs[VLAN_SERVICE_ADDITIONAL_INFO_ATTR]
        is_auto = istrue(attrs[VLAN_SERVICE_AUTO_ATTR])
        if VLAN_SERVICE_MANAGEMENT_VLAN_ATTR in attrs:
            is_management_vlan = istrue(attrs[VLAN_SERVICE_MANAGEMENT_VLAN_ATTR])

        resdet = self.testshell.GetReservationDetails(self.resid).ReservationDescription

        newly_reserved = []

        self.testshell.write_message(self.resid, 'Add VLAN started')

        if service_vlan_id == '':
            if VLAN_SERVICE_VLAN_RANGE_ATTR in attrs:
                service_vlan_id = attrs[VLAN_SERVICE_VLAN_RANGE_ATTR]

        if service_vlan_id == '':
            service_vlan_id = '-1'

        if is_updating:
            if update_vlan_id != '':
                service_vlan_id = update_vlan_id
            if update_vlan_share != service_share_vlan:
                service_share_vlan = update_vlan_share

        if not is_auto:
            self.assert_vlan_id_valid(service_mode, service_vlan_id)

        vlan_available_in_resource_pool = False

        if not is_management_vlan:
            poolname = self.domain+' VLAN Pool'
            try:
                self.testshell.GetResourceDetails(poolname)
            except:
                raise Exception('VLAN service {0}: No VLAN pool "{1}" was defined'.format(self.service_name, poolname))

            auto_vlan_already_allocated = False

            if service_vlan_id == '-1' and is_auto:
                service_vlan_id = self.get_first_vlan_from_pool()
                if service_vlan_id == '-1':
                    vlan_available_in_resource_pool = False
                else:
                    vlan_available_in_resource_pool = self.check_vlan_availability_in_vlan_pool(service_vlan_id)

            auto_vlan_already_allocated = False
            successfully_reserved = False
            if is_auto:
                if vlan_available_in_resource_pool:
                    self.testshell.SetServiceAttributesValues(self.resid, self.service_name, [AttributeNameValue(VLAN_SERVICE_VLAN_ID_ATTR, service_vlan_id)])
                    more_than_once, priority_to_allocate = self.used_more_than_once(service_vlan_id, self.service_name)
                    auto_vlan_already_allocated = more_than_once and not priority_to_allocate

                    ffn = 0
                    if auto_vlan_already_allocated:
                        vlan_available_in_resource_pool = False
                        ffn = 2
                    else:
                        toreserve, newly_reserved, haderrors = self.reserve_vlan_from_pool(service_vlan_id, service_share_vlan)
                        if haderrors:
                            self.testshell.SetServiceAttributesValues(self.resid, self.service_name, [AttributeNameValue(VLAN_SERVICE_VLAN_ID_ATTR, '')])
                            vlan_available_in_resource_pool = False
                            self.testshell.RemoveResourcesFromReservation(self.resid, toreserve)
                            ffn = 3
                        else:
                            successfully_reserved = True
                    if ffn > 0:
                        exit_loop = False
                        index = 1
                        while index < ffn and not exit_loop:
                            if service_vlan_id == '-1' and is_auto:
                                service_vlan_id = self.get_first_vlan_from_pool()
                            if service_vlan_id == '-1':
                                vlan_available_in_resource_pool = False
                            else:
                                vlan_available_in_resource_pool = self.check_vlan_availability_in_vlan_pool(service_vlan_id)
                            if is_auto and vlan_available_in_resource_pool:
                                self.testshell.SetServiceAttributesValues(self.resid, self.service_name, [AttributeNameValue(VLAN_SERVICE_VLAN_ID_ATTR, service_vlan_id)])
                            more_than_once, priority_to_allocate = self.used_more_than_once(service_vlan_id, self.service_name)
                            auto_vlan_already_allocated = more_than_once and not priority_to_allocate
                            if not auto_vlan_already_allocated:
                                vlan_available_in_resource_pool = True
                                toreserve, newly_reserved, haderrors = self.reserve_vlan_from_pool(service_vlan_id, service_share_vlan)
                                if haderrors:
                                    self.testshell.SetServiceAttributesValues(self.resid, self.service_name, [AttributeNameValue(VLAN_SERVICE_VLAN_ID_ATTR, '')])
                                    self.testshell.RemoveResourcesFromReservation(self.resid, toreserve)
                                    vlan_available_in_resource_pool = False
                                else:
                                    vlan_available_in_resource_pool = True
                                    successfully_reserved = True
                                    exit_loop = True
                            else:
                                vlan_available_in_resource_pool = False
                            index += 1
                        if ffn == 2 and not exit_loop:
                            self.testshell.write_message(self.resid, 'VLAN service {0}: Could not find VLAN or VLAN is not available'.format(self.service_name))

            else:
                toreserve, newly_reserved, haderrors = self.reserve_vlan_from_pool(service_vlan_id, service_share_vlan)
                if haderrors:
                    self.testshell.RemoveResourcesFromReservation(self.resid, toreserve)
                    vlan_available_in_resource_pool = False
                    raise Exception('VLAN service {0}: Could not reserve VLAN {1} from pool'.format(self.service_name, service_vlan_id))
                else:
                    successfully_reserved = True

        errors = []
        successfully_added_duts = []
        if is_management_vlan or vlan_available_in_resource_pool:
            l1_duts = []
            for dut2 in duts:
                try:
                    self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                                   self.testshell.get_root_resource(dut2),
                                                                   add_vlan_command_name,
                                                                   vlan_command_tag,
                                                                   [service_mode, service_vlan_id, service_additional_info],
                                                                   [dut2],
                                                                   printOutput=True)
                    self.testshell.UpdateConnectorAliasInReservation(self.resid, dut2, self.service_name, 'bi', 'VLAN Created')
                    successfully_added_duts.append(dut2)
                except:
                    if self.is_resource_connected_to_l1(dut2):
                        l1_duts.append(dut2)
                    else:
                        errors.append('VLAN service {0}: DUT {1} did not have remote command {2} and was not connected to an L1'.format(self.service_name, dut2, add_vlan_command_name))
            duts_on_not_available_vlans = set()
            duts_on_available_vlans = set()
            duts_on_all_vlans = []
            for conn in resdet.Connectors:
                x = None
                if conn.Source == self.service_name:
                    x = conn.Target
                if conn.Target == self.service_name:
                    x = conn.Source
                if x is not None:
                    duts_on_all_vlans.append(x)
                    if conn.Alias == 'N/A VLAN':
                        duts_on_not_available_vlans.add(x)
                    if conn.Alias == 'VLAN Created':
                        duts_on_available_vlans.add(x)

            if len(l1_duts) > 0:
                for l1_dut in l1_duts:
                    if len(duts_on_not_available_vlans) > 0 or len(duts_on_available_vlans) > 0:
                        for dut2 in duts_on_all_vlans:
                            if l1_dut != dut2:
                                if self.configure_partner(l1_dut, dut2, add_vlan_command_name, vlan_command_tag, service_mode, service_vlan_id, service_additional_info, errors):
                                    successfully_added_duts.append(l1_dut)
                                    break
                    else:
                        self.testshell.UpdateConnectorAliasInReservation(self.resid, l1_dut, self.service_name, 'bi', 'N/A VLAN')

            duts_on_available_vlans = []
            duts_on_not_available_vlans = []
            for conn in self.testshell.GetReservationDetails(self.resid).ReservationDescription.Connectors:
                x = None
                if conn.Source == self.service_name:
                    x = conn.Target
                if conn.Target == self.service_name:
                    x = conn.Source
                if x is not None:
                    if conn.Alias == 'N/A VLAN':
                        duts_on_not_available_vlans.append(x)
                    if conn.Alias == 'VLAN Created':
                        duts_on_available_vlans.append(x)

            duts_on_available_vlans += successfully_added_duts

            if len(duts_on_available_vlans) > 0:
                self.testshell.write_message(self.resid, 'VLAN service {0}: Configuring N/A VLANs {1}'.format(self.service_name, ', '.join(duts_on_not_available_vlans)))
                dut_to_config_with = duts_on_available_vlans[0]
                for dut in duts_on_not_available_vlans:
                    if self.configure_partner(dut, dut_to_config_with, add_vlan_command_name, vlan_command_tag, service_mode, service_vlan_id, service_additional_info, errors):
                        successfully_added_duts.append(dut)
            else:
                if len(duts_on_not_available_vlans) > 1:
                    dut_to_config_with = duts_on_not_available_vlans[-1]
                    for dut in duts_on_not_available_vlans:
                        if dut != dut_to_config_with:
                            if self.configure_partner(dut, dut_to_config_with, add_vlan_command_name, vlan_command_tag, service_mode, service_vlan_id, service_additional_info, errors):
                                successfully_added_duts.append(dut)
                    if self.configure_partner(dut_to_config_with, duts_on_not_available_vlans[0], add_vlan_command_name, vlan_command_tag, service_mode, service_vlan_id, service_additional_info, errors):
                        successfully_added_duts.append(dut_to_config_with)

        if not is_management_vlan:
            if len(errors) == 0:
                self.testshell.SetResourceSharedState(self.resid, duts, False)
                self.testshell.LockResources(self.resid, duts)
            else:
                if is_auto and service_vlan_id == '':
                    self.testshell.SetServiceAttributesValues(self.resid, self.service_name, [AttributeNameValue(VLAN_SERVICE_VLAN_ID_ATTR, '')])
                self.testshell.RemoveResourcesFromReservation(self.resid, newly_reserved)
        self.testshell.write_message(self.resid, 'Add VLAN ended\n------------------------------------------------------------\n')

    def configure_partner(self, thisdut, otherdut, add_vlan_command_name, vlan_command_tag, service_mode, service_vlan_id, service_additional_info, errors):
        is_found_l2, found_switch, found_switch_address, switch_to_activate_driver = self.configure_route_for_dut(thisdut, otherdut)
        if is_found_l2:
            resource_to_run_command_on = self.testshell.get_connected_resource(found_switch)
            child, root = self.testshell.get_resource_name_and_root(resource_to_run_command_on)
            self.testshell.AddResourcesToReservation(self.resid, [child, root])
            try:
                self.testshell.ExecuteResourceConnectedCommand(self.resid,
                                                               root,
                                                               add_vlan_command_name,
                                                               vlan_command_tag,
                                                               [service_mode, service_vlan_id, service_additional_info],
                                                               [child],
                                                               printOutput=True)
                self.testshell.UpdateConnectorAliasInReservation(self.resid, thisdut, self.service_name, 'bi', 'VLAN Created')
                return True
            except Exception as ex:
                errors.append('VLAN service {0}: DUT {1}: Failed to run remote command {2} on found L2 switch {3}: {4}'.format(self.service_name, thisdut, add_vlan_command_name, root, str(ex)))
        return False

    def check_vlan_availability_in_vlan_pool(self, service_vlan_id):
        resd = self.testshell.GetReservationDetails(self.resid).ReservationDescription
        vlans = self.get_all_vlans_from_vlan_id_input(service_vlan_id)
        vlan_pool_resource_name = self.domain + ' VLAN Pool'
        vlan_pool_subresource_name = self.domain + ' VLAN Pool/VLAN '
        # rd = self.testshell.GetResourceDetails(vlan_pool_resource_name, showAllDomains=False)
        # rd.Name
        # rd.Locked
        # rd.LockInfo.ReservationName
        # rd.Excluded
        errors = []
        for vlan in vlans:
            v = vlan_pool_subresource_name + str(vlan)
            firstrow = True
            excluded = False
            unshared_in_other_reservation = False
            for r in self.testshell.GetResourceAvailabilityInTimeRange(v, resd.StartTime, resd.EndTime, showAllDomains=False).Resources:
                for res in r.Reservations:
                    if res.ReservationId != self.resid and not res.Shared:
                        unshared_in_other_reservation = True
                if r.Excluded and firstrow:
                    excluded = True
                firstrow = False
            if excluded or unshared_in_other_reservation:
                errors.append('VLAN {0} is not available'.format(v))

        self.testshell.write_message(self.resid, '\n'.join(errors))

        return len(errors) == 0

    def get_first_vlan_from_pool(self):
        vlan_pool_resource_name = self.domain + ' VLAN Pool'
        vlan_pool_subresource_name = self.domain + ' VLAN Pool/VLAN '
        found_vlan_id = '-1'
        resd = self.testshell.GetReservationDetails(self.resid).ReservationDescription
        tocheck = []
        for ch in self.testshell.GetResourceDetails(vlan_pool_resource_name).ChildResources:
            if not ch.Locked and not ch.Excluded:
                tocheck.append(ch.Name)
        step = 50
        from_index = 0
        to_index = 0
        last_index = len(tocheck)

        if to_index + step < last_index:
            to_index += step
        else:
            to_index = last_index - 1

        while from_index <= last_index - 1 and found_vlan_id == '-1':
            bulked = tocheck[from_index:to_index]
            hh = []
            for r in self.testshell.GetResourceAvailabilityInTimeRange(bulked, resd.StartTime, resd.EndTime, showAllDomains=False).Resources:
                if r.ReservedStatus == 'Not In Reservations':
                    hh.append(r.FullName)
            if len(hh) > 0:
                found_vlan_id = hh[random.randint(0, len(hh) - 1)].replace(vlan_pool_subresource_name, '')
            else:
                found_vlan_id = '-1'

            from_index = to_index + 1
            if from_index + step < last_index:
                to_index = to_index + 1 + step
            else:
                to_index = last_index - 1
        if found_vlan_id == '-1':
            self.testshell.write_message(self.resid, "Couldn't find available VLAN")
        return found_vlan_id

    @DriverFunction
    def connect_all(self, matrix_json):
        self.ensure_testshell(matrix_json)

        duts = []
        for c in self.testshell.GetReservationDetails(self.resid).ReservationDescription.Connectors:
            if c.Alias == '':
                if self.service_name == c.Target:
                    duts.append(c.Source)
                if self.service_name == c.Source:
                    duts.append(c.Target)

        self.validate_endpoint_not_connected_to_vlan_service(duts)

        self.create_vlan(matrix_json, duts, update_vlan_id='', update_vlan_share=False, is_updating=False)

    def assert_vlan_id_valid(self, service_mode, service_vlan_id):
        if service_mode.lower() == 'access':
            if not service_vlan_id.isdigit():
                raise Exception('VLAN id should be numeric but was "{0}"'.format(service_vlan_id))
        else:
            if not re.match(r'[-,0-9][-,0-9]*', service_vlan_id):
                raise Exception('VLAN id should be comma-separated numbers or ranges in the form 1-2,5,6-7 but was "{0}"'.format(service_vlan_id))

    def is_resource_connected_to_l1(self, dut):
        for conn in self.testshell.GetResourceDetails(dut, False).Connections:
            if conn.FullPath != '':
                attrs = self.testshell.get_resource_attributes(self.testshell.get_root_resource(conn.FullPath))
                return attrs['family'].lower() == 'l1'
        return False

    def configure_route_for_dut(self, thisdut, otherdut):
        for route in self.testshell.GetRoutesSolution(self.resid, [thisdut], [otherdut], 'bi', 100, False).Routes:
            for segment in route.Segments:
                for x in [segment.Source, segment.Target]:
                    attrs = self.testshell.get_resource_attributes(x)
                    if 'L2 Switch Type' in attrs and attrs['L2 Switch Type'] not in ['', 'None']:
                        return True, attrs['name'], attrs['address'], attrs['name'].split('/')[0]
        return False, None, None, None

    def configure_route_for_dut_remove(self, first_dut, second_dut):
        is_found_l2, l2_full_name, address, to_run_on= self.get_connected_l2_and_unmap_l1s(first_dut)
        return is_found_l2, l2_full_name

    def get_connected_l2_and_unmap_l1s(self, dut):
        rd = self.testshell.GetResourceDetails(dut, showAllDomains=False)
        connected_to = None
        for conn in rd.Connections:
            if conn.FullPath != '':
                connected_to = conn.FullPath
                break
        childport, root = self.testshell.get_resource_name_and_root(connected_to)
        rdroot = self.testshell.GetResourceDetails(root)
        family = rdroot.ResourceFamilyName
        for conn in rdroot.Connections:
            if conn.FullPath != '':
                root_connection = conn.FullPath
                break
        end_loop = False

        currport = childport
        is_l2 = False
        while (('patch' in family) or ('l1' in family)) and not end_loop:
            mappings = self.testshell.GetResourceMappings([currport]).Mapping
            if len(mappings) > 0:
                self.testshell.UnMapPorts(currport, mappings[0].Target)
                mdt = self.testshell.GetResourceDetails(mappings[0].Target, showAllDomains=False)
                found = False
                for conn in mdt.Connections:
                    if conn.FullPath != '':
                        currport = conn.FullPath
                        found = True
                        break
                self.testshell.UpdateConnectionWeight(mappings[0].Target, currport, 10)
                cdt = self.testshell.GetResourceDetails(currport, showAllDomains=False)
                cdtroot = cdt.Name.split('/')[0]
                ddt = self.testshell.GetResourceDetails(cdtroot, showAllDomains=False)
                family = ddt.ResourceFamilyName
                is_l2 = False
                for a in ddt.ResourceAttributes:
                    if a.Name == 'L2 Switch Type' and a.Value != 'None':
                        is_l2 = True
                        break
            else:
                end_loop = True
        is_found_l2 = is_l2
        l2_full_name = currport
        l2dt = self.testshell.GetResourceDetails(l2_full_name, showAllDomains=False)
        connected_to_l1_name = None
        for conn in l2dt.Connections:
            if conn.FullPath != '':
                connected_to_l1_name = conn.FullPath
                break
        ch, ro = self.testshell.get_resource_name_and_root(connected_to_l1_name)
        return is_found_l2, l2_full_name, connected_to_l1_name, ro

    def get_all_vlans_from_vlan_id_input(self, vlan_id):
        rv = []
        for r in vlan_id.split(','):
            if '-' in r:
                start, end = r.split('-')
                for j in range(int(start), int(end) + 1):
                    rv.append(j)
            else:
                rv.append(int(r))
        return rv

    def reserve_vlan_from_pool(self, service_vlan_id, service_share_vlan):
        requested_vlans = self.get_all_vlans_from_vlan_id_input(service_vlan_id)
        vlan_pool_resource_name = self.domain + ' VLAN Pool'
        vlan_pool_subresource_name = self.domain + ' VLAN Pool/VLAN '
        reserved_resources = []
        rd = self.testshell.GetReservationDetails(self.resid).ReservationDescription
        for r in rd.Resources:
            if r.ResourceFamilyName == 'VLAN ID':
                reserved_resources.append(r.Name)

        newly_added_resources = []
        toreserve = []

        for requested_vlan in requested_vlans:
            v = vlan_pool_subresource_name + str(requested_vlan)
            if v not in reserved_resources:
                newly_added_resources.append(v)
            toreserve.append(requested_vlan)

        haderrors = len(self.testshell.AddResourcesToReservation(self.resid, toreserve).Conflicts) > 0
        if not service_share_vlan:
            for r2 in self.testshell.GetResourceAvailabilityInTimeRange(toreserve, rd.StartTime, rd.EndTime, showAllDomains=False).Resources:
                if len(r2.Reservations) > 0 and r2.Reservations[0].ReservationId == self.resid:
                    try:
                        self.testshell.SetResourceSharedState(self.resid, toreserve, service_share_vlan)
                    except:
                        haderrors = True

        return toreserve, newly_added_resources, haderrors

    def used_more_than_once(self, service_vlan_id, service_name):
        priority = False
        first_auto_service = True
        n = 0
        for service in self.testshell.GetReservationDetails(self.resid).ReservationDescription.Services:
            if service.ServiceName == 'Auto VLAN':
                if service.Alias == service_name:
                    if first_auto_service:
                        priority = True
                    for attr in service.Attributes:
                        if attr.Name == VLAN_SERVICE_VLAN_ID_ATTR and attr.Value == service_vlan_id:
                            n += 1
                first_auto_service = False

        return n > 1, priority

    def check_endpoints(self, added_connections, removed_connections):
        resd = self.testshell.GetReservationDetails(self.resid).ReservationDescription
        if len(added_connections) > 0:
            for service in resd.Services:
                for ac in added_connections:
                    if service.Alias == ac[0] and service.Alias == ac[1]:
                        return False
        if len(removed_connections) > 0:
            for service in resd.Services:
                for ac in removed_connections:
                    if service.Alias == ac[0] and service.Alias == ac[1]:
                        return False
        return True

