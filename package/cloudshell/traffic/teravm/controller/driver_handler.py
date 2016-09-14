from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import time
import requests
import paramiko
from retrying import retry, RetryError
import tempfile
import re
import os
import xml.etree.ElementTree as ET

from cloudshell.shell.core.driver_context import AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session, get_attribute_value
from cloudshell.traffic.teravm.common.vsphere_helper import get_vsphere_credentials
from cloudshell.traffic.teravm.common import i18n as c
from cloudshell.traffic.teravm.controller.port_selector_helper import *
from cloudshell.traffic.teravm.controller.teravm_executive_helper import *

CLOUDSHELL_TEST_CONFIGURATION = 'CloudshellConfiguration'


def retry_if_result_none(result):
    """Return True if we should retry (in this case when result is None), False otherwise"""
    return result is False


class TVMControllerHandler:
    TVM_TEST_PATH = 'qs_tests'
    TVM_TM_INTERFACE_MODEL = {
        'ResourceFamilyName': 'Virtual Traffic Generator Port',
        'ResourceModelName': 'TeraVM Interface'
    }

    FAILED_TO_IMPORT_MSG = 'Could not import test group.\nPlease contact your administrator.'
    FAILED_TO_START_MSG = 'Could not start test group.\nPlease contact your administrator.'

    def __init__(self, cli_service):
        self.cli = cli_service

    def load_configuration(self, context, test_location):
        api = get_cloudshell_session(context)
        reservation_id = context.reservation.reservation_id
        reservation = api.GetReservationDetails(reservation_id).ReservationDescription

        interfaces = self._get_available_interfaces_from_reservation(reservation, api)
        self._reserve_active_ports(interfaces, context.reservation.owner_user)
        file_name = self._prepare_test_group_file(test_location, interfaces, context.reservation.owner_user,
                                                  reservation_id, api)
        self._import_test_group(file_name, context.reservation.owner_user, reservation_id, api)

    def run_test(self, context):
        api = get_cloudshell_session(context)
        reservation_id = context.reservation.reservation_id
        try:
            self._start_test_group(CLOUDSHELL_TEST_CONFIGURATION, context.reservation.owner_user, reservation_id, api)
        except Exception as e:
            self.prettify_exception(e)

    @staticmethod
    def prettify_exception(e):
        if len(e.args) > 1:
            try:
                e = Exception('\n'.join(e.args))
            except:
                pass
        raise e

    def stop_test(self, context):
        api = get_cloudshell_session(context)
        reservation_id = context.reservation.reservation_id
        self.cli.send_command('cli -u {0} stopTestGroup //{1}'.format(context.reservation.owner_user,
                                                                      CLOUDSHELL_TEST_CONFIGURATION),
                              retries=1,
                              timeout=90)
        self._message('+ Stopped ' + CLOUDSHELL_TEST_CONFIGURATION, reservation_id, api)

    def run_custom_command(self, context, command_text):
        return self.cli.send_command(command_text)

    @staticmethod
    def get_inventory(context):
        api = get_cloudshell_session(context, 'Global')

        resource = api.GetResourceDetails(context.resource.fullname)
        vmuid = resource.VmDetails.UID
        license_server_ip = next((attr.Value for attr in resource.VmDetails.VmCustomParams
                                  if attr.Name == c.KEY_LICENSE_SERVER))

        vcenter_address, vsphere_password, vsphere_user = get_vsphere_credentials(api, resource)
        vsphere = pyVmomiService(SmartConnect, Disconnect, task_waiter=None)
        si = vsphere.connect(vcenter_address, vsphere_user, vsphere_password)
        controller_ip = _get_test_controller_management_ip(vmuid, si, vsphere)
        api.UpdateResourceAddress(resource.Name, controller_ip)

        while not _controller_configured_with_license_server(controller_ip, license_server_ip):
            _license_tvm_controller(controller_ip, license_server_ip)

        api.SetResourceLiveStatus(resource.Name, 'Online', 'Active')
        return AutoLoadDetails([], [])

    def _start_test_group(self, test_name, user_name, reservation_id, api):
        self.cli.send_command('cli -u {0} startTestGroup //{1}'.format(user_name, test_name), retries=1, timeout=90)
        self._message('Started ' + test_name, reservation_id, api)

    def _import_test_group(self, file_name, user_name, reservation_id, api):
            self.cli.send_command(
                'cli -u {0} importTestGroup // {1}/{2}'.format(user_name, self.TVM_TEST_PATH, file_name)
            )
            self._message('+ Imported test group', reservation_id, api)

    def _prepare_test_group_file(self, test_path, interfaces, user_name, reservation_id, api):
        modified_test_path = self._generate_test_file_with_replaced_interfaces(test_path, interfaces)
        self._delete_test_group_if_exists(CLOUDSHELL_TEST_CONFIGURATION, user_name, reservation_id, api)
        file_name = self._copy_test_group_file(modified_test_path)
        return file_name

    def _copy_test_group_file(self, modified_test_path):
        self.cli.send_command('test -d {0}||mkdir {0}'.format(self.TVM_TEST_PATH))
        self.cli.send_file(modified_test_path, self.TVM_TEST_PATH)
        file_dir, file_name = os.path.split(modified_test_path)
        return file_name

    def _cancel_start_test_if_test_is_running(self, test_name, reservation_id, api):
        try:
            if self._is_test_running(test_name):
                self._message('{0} is already running. Only a single instance can run'.format(test_name),
                              reservation_id, api)
                raise Exception('\n' + test_name + ' is already running')
        except RetryError:
            pass

    def _delete_test_group_if_exists(self, test_name, user_name, reservation_id, api):
        try:
            self.cli.send_command('cli -u {0} deleteTestGroup //{1}'.format(user_name, test_name))
            self._message('+ Deleted test group with same name from controller', reservation_id, api)
        except:
            self.cli.send_command('\n')
            pass

    def _cancel_start_test_group_gracefully(self, e, test_name, user_name, reservation_id, api):
        try:
            self._message('~ An error occurred, stopping test. Please contact your administrator', reservation_id, api)
            self.cli.send_command('cli -u {0} stopTestGroup {1}'.format(user_name, test_name), retries=1, timeout=90)
            self._message('~ Test execution cancelled.', reservation_id, api)
        finally:
            if len(e.args) > 1:
                self._message(' ~ Failed command returned: \n\n {0}'.format(e.args[1]), reservation_id, api)
                raise Exception(e.args[0])  # hacky way to show only the main message.
            raise e

    @staticmethod
    def _get_available_interfaces_from_reservation(reservation, api):
        def get_as_tvm_interface(address):
            parts = address.split('/')
            # '00:50:56:00:00:06' => '006' ==> 6 ==> '6'
            module_id = str(int(parts[0][-4:].replace(':', ''), 16))
            agent_id = '1'
            port_id = parts[1]
            return '/'.join([module_id, agent_id, port_id])

        test_modules = [api.GetResourceDetails(res.Name) for res in reservation.Resources
                        if res.ResourceModelName == c.TEST_MODULE_MODEL]

        ports = []
        for mod in test_modules:
            module_ports = [res for res in mod.ChildResources if res.ResourceModelName == c.TEST_MODULE_PORT_MODEL
                            and c.COMMS_INTERFACE not in res.Name]
            mac = mod.FullAddress.split('/').pop()
            for port in module_ports:
                port.tvm_executive = get_attribute_value(c.ATTRIBUTE_NAME_TVM_EXECUTIVE, mod)
                port.mac = mac
            ports.extend(module_ports)

        for port in ports:
            port.interface_id = get_as_tvm_interface(port.FullAddress)
            port.logical_name = get_attribute_value(c.ATTRIBUTE_NAME_LOGICAL_NAME, port).lower().strip()

        return ports

    @staticmethod
    def _reserve_active_ports(interfaces, user_name):
        pool_manager_addresses = {interface.tvm_executive for interface in interfaces}
        macs = {interface.mac for interface in interfaces}
        if len(pool_manager_addresses) > 1:
            raise Exception('Cannot execute test on TVM test module interfaces from different pool managers!'
                            'Interfaces have these pool manager ids' + ', '.join(pool_manager_addresses))
        pool_manager_address = pool_manager_addresses.pop()
        interface_tvm_resource_ids = get_interface_tvm_resource_ids(macs, pool_manager_address)
        reserve_interfaces_in_pool_manager(interface_tvm_resource_ids, user_name, pool_manager_address)

    @retry(stop_max_attempt_number=5, wait_fixed=5000)
    def _get_first_running_test(self, reservation_id, api):
        test_name = None
        self._clear_console_buffer()
        command = 'cli showRunningTestGroup'
        out = self.cli.send_command(command)
        if out:
            p = '\d+\s\w+\s(\/\/.*)\n'  # '1 admin //new_test' test number, username, test name
            result = re.search(p, out)
            if result:
                test_name = result.group(1)
        if test_name is None:
            raise Exception('Could not find a running test')
        self._message('+ Found running test: ' + test_name, reservation_id, api)
        return test_name

    def _clear_console_buffer(self):
        self.cli._session = None

    @retry(retry_on_result=retry_if_result_none, stop_max_attempt_number=5, wait_fixed=750)
    def _is_test_running(self, test_name):
        command = 'cli showRunningTestGroup'
        out = self.cli.send_command(command)
        p = '\d+\s\w+\s(\/\/.*{0})\n'.format(test_name)
        result = re.search(p, out)
        return result is not None

    def _get_test_name(self, test_file_path, reservation_id, api):
        tree = ET.parse(test_file_path)
        root = tree.getroot()
        name = root.findall('./test_group/name')
        test_group_name = name[0].text
        self._message('+ Test group name is ' + test_group_name, reservation_id, api)
        return test_group_name

    def _generate_test_file_with_replaced_interfaces(self, test_file_path, ports):
        config = self._generate_test_configuration_with_replaced_interfaces(test_file_path, ports)
        temp_file_path = tempfile.mktemp()
        config.write(temp_file_path)
        return temp_file_path

    def _generate_test_configuration_with_replaced_interfaces(self, test_file_path, ports):
        tree = ET.parse(test_file_path)
        root = tree.getroot()

        interface_elements = self._get_interface_elements_from_xml(root)

        # Selecting which port interface replaces which configuration interface:
        # First, select by logical name equivalent to *virtual host name* that is parent of interface
        # If not, select by logical name equivalent to interface id, 1/2/3
        # If not, select arbitrarily a port

        available_ports = list(ports)

        interfaces_count = len(interface_elements)
        if len(ports) < interfaces_count:
            raise Exception('Not enough free ports to for test configuration. Need {0} ports'.format(interfaces_count))

        populate_free_interfaces_by_test_element_name(interface_elements, available_ports)
        populate_free_interfaces_by_test_element_interface(interface_elements, available_ports)
        populate_free_interfaces_arbitrarily(interface_elements, available_ports)

        name = root.find('./test_group/name')
        name.text = CLOUDSHELL_TEST_CONFIGURATION

        return tree

    @staticmethod
    def _get_interface_elements_from_xml(root):
        interface_elements = []
        virtual_hosts = root.findall('.//direct_virtual_host')
        for virtual_host in virtual_hosts:
            interfaces = virtual_host.findall('.//interface')
            virtual_host_name = virtual_host.find('name').text
            for interface in interfaces:
                if not hasattr(interface, 'text') and interface.text.startswith('\n'):
                    continue
                interface.virtual_host_name = virtual_host_name.lower().strip()
            interface_elements.extend(interfaces)

        return interface_elements

    @staticmethod
    def _message(message, reservation_id, api):
        api.WriteMessageToReservationOutput(reservation_id, message)

###############################################
###############################################
#              |    |    |                    #
#              )_)  )_)  )_)                  #
#             )___))___))___)\                #
#            )____)____)_____)\\              #
#          _____|____|____|____\\\__          #
# ---------\                   /---------     #
#   ^^^^^ ^^^^^^^^^^^^^^^^^^^^^               #
#     ^^^^      ^^^^     ^^^    ^^            #
#          ^^^^      ^^^                      #
###############################################
###############################################


def _get_test_controller_management_ip(vmuid, si, vsphere, timeout=120):
    expired = time.time() + timeout
    while True:
        if time.time() > expired:
            raise Exception('Could not find controller management ip for controller ' + vmuid)
        try:
            vm = vsphere.get_vm_by_uuid(si, vmuid)
            controller_management_ip = vm.guest.net[1].ipAddress[0]
            return controller_management_ip
        except:
            print 'Waiting for controller management ip...'
            time.sleep(10)


def _controller_configured_with_license_server(controller_management_ip, license_server_ip):
    try:
        lic_url = 'https://{0}/teraVM/postInstallConfiguration'.format(controller_management_ip)
        r = requests.get(lic_url, verify=False)
        return license_server_ip in r.content
    except:
        raise Exception('Was not able to access controller through HTTPS')


def _license_tvm_controller(controller_management_ip, license_server_ip):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=controller_management_ip, username=c.CONTROLLER_SSH_USER,
                    password=c.CONTROLLER_SSH_PASSWORD)
        stdin, stdout, stderr = ssh.exec_command(str.format(
            'cli configureTvmLicensing LicenseServer {0} {1} {2}', license_server_ip, '5053', '5054'))
        print stdout.readlines()
        ssh.close()

