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
from scp import SCPClient

from cloudshell.shell.core.driver_context import AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.traffic.teravm.common.vsphere_helper import get_vsphere_credentials
from cloudshell.traffic.teravm.common import i18n as c
from cloudshell.cli.service.cli_service import CliService

from debug_utils import debugger


def retry_if_result_none(result):
    """Return True if we should retry (in this case when result is None), False otherwise"""
    return result is False


class TVMControllerHandler:
    TVM_TEST_PATH = 'qs_tests'
    TVM_TM_INTERFACE_MODEL = {
        'ResourceFamilyName': 'Virtual Traffic Generator Port',
        'ResourceModelName': 'TeraVM Interface'
    }

    def __init__(self):
        self.uploaded_test_name = ''
        self.cli = CliService()
        self.cli.send_file = send_file
        self.user_name = ''
        self.reservation_id = ''

    def _run_before(self, context):
        self.user_name = context.reservation.owner_user
        self.testshell_api = get_cloudshell_session(context)
        resid = context.reservation.reservation_id
        self.reservation = self.testshell_api.GetReservationDetails(resid).ReservationDescription

    def preview_configuration(self, context, test_location):
        debugger.attach_debugger()
        self._run_before(context)
        self.uploaded_test_name, file_name = self._prepare_test_group_file(test_location)
        pass

    def load_configuration(self, context, test_location, interfaces):
        self.user_name = context.reservation.owner_user
        self.uploaded_test_name, file_name = self._prepare_test_group_file(test_location)
        # self.register_active_ports()
        # self.cancel_running_test_if_is_test_group(self.uploaded_test_name)
        # self.import_test_group(file_name)
        pass

    def run_test(self, context):
        self.user_name = context.reservation.owner_user
        # if self.uploaded_test_name == '':
        #     raise Exception('No test group was uploaded!')
        # try:
        #     self.run_stuff(self.uploaded_test_name)
        # except Exception as e:
        #     self.cancel_test_gracefully(e, self.uploaded_test_name)
        pass

    def stop_test(self, context):
        self.user_name = context.reservation.owner_user
        # self.stop_all_tests()
        pass

    @staticmethod
    def run_custom_command(context):
        pass

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

    def _prepare_test_group_file(self, test_path):
        interfaces = self._get_available_interfaces_from_reservation()
        modified_test_path = self._generate_test_file_with_appropriate_interfaces(test_path, interfaces)
        test_name = self._get_test_name(modified_test_path)
        self._delete_test_group_if_exists(test_name)
        file_name = self._copy_test_group_file(modified_test_path)
        return file_name, test_name

    def _copy_test_group_file(self, modified_test_path):
        self.cli.send_command('test -d {0}||mkdir qs_tests'.format(self.TVM_TEST_PATH))
        self.cli.send_file(modified_test_path, self.TVM_TEST_PATH)
        file_dir, file_name = os.path.split(modified_test_path)
        return file_name

    def _delete_test_group_if_exists(self, test_name):
        try:
            self.cli.send_command('cli -u {0} deleteTestGroup //{1}'.format(self.user_name, test_name))
            self._message('+ Deleted test group with same name from controller')
        except:
            self.cli.send_command('\n')
            pass

    def _cancel_start_test_group_gracefully(self, e, test_name):
        try:
            self._message('~ An error occurred, stopping test. Please contact your administrator')
            self.cli.send_command('cli -u {0} stopTestGroup {1}'.format(self.user_name, test_name))
            self._message('~ Test execution cancelled.')
        finally:
            if len(e.args) > 1:
                self._message(' ~ Failed command returned: \n\n {0}'.format(e.args[1]))
                raise Exception(e.args[0])  # hacky way to show only the main message.
            raise e

    def _get_available_interfaces_from_reservation(self):
        def get_as_tvm_interface(address):
            parts = address.split('/')
            # '00:50:56:00:00:06' => '006' ==> 6 ==> '6'
            module_id = str(int(parts[0][-4:].replace(':', ''), 16))
            agent_id = '1'
            port_id = parts[1]
            return '/'.join([module_id, agent_id, port_id])

        test_modules = [self.testshell_api.GetResourceDetails(res.Name) for res in self.reservation.Resources
                        if res.ResourceModelName == c.TEST_MODULE_MODEL]

        ports = []
        for mod in test_modules:
            ports.extend([res for res in mod.ChildResources if res.ResourceModelName == c.TEST_MODULE_PORT_MODEL])

        for port in ports:
            port.interface_id = get_as_tvm_interface(port.FullAddress)
            port.logical_name = \
                (att.Value for att in port.ResourceAttributes if att.Name == c.ATTRIBUTE_NAME_LOGICAL_NAME).next()\
                    .lower().trim()

        return ports

    @retry(stop_max_attempt_number=5, wait_fixed=5000)
    def _get_first_running_test(self):
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
        self._message('+ Found running test: ' + test_name)
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

    def _get_test_name(self, test_file_path):
        tree = ET.parse(test_file_path)
        root = tree.getroot()
        name = root.findall('./test_group/name')
        test_group_name = name[0].text
        self._message('+ Test group name is ' + test_group_name)
        return test_group_name

    def _generate_test_file_with_appropriate_interfaces(self, test_file_path, ports):
        tree = ET.parse(test_file_path)
        root = tree.getroot()
        port_targets = [port.logical_name for port in ports]

        interface_elements = []
        virtual_hosts = root.findall('.//direct_virtual_host')
        for virtual_host in virtual_hosts:
            interfaces = virtual_host.findall('.//interface')
            virtual_host_name = virtual_host.find('name').text
            for interface in interfaces:
                if interface.text.startswith('\n'):
                    continue
                interface.virtual_host_name = virtual_host_name.lower().trim()
            interface_elements.extend(interfaces)

        # Selecting which port interface replaces which configuration interface:
        # First, select by logical name equivalent to virtual host name that is parent of interface
        # If not, select by logical name equivalent to interface id, 1/2/3
        # If not, select arbitrarily a port

        for element in list(interface_elements):
            if element.virtual_host_name in port_targets:
                for port in ports:
                    if port.logical_name == element.virtual_host_name:
                        element.text = port.interface_id
                        ports.remove(port)
                        break
                interface_elements.remove(element)
                continue

        for element in list(interface_elements):
            if element.text in port_targets:
                for port in ports:
                    if port.logical_name == element.text:
                        element.text = port.interface_id
                        ports.remove(port)
                        break
                continue

        for element in interface_elements:
            port = ports.pop()
            element.text = port.interface_id

        temp_file_path = tempfile.mktemp()
        tree.write(temp_file_path)
        self._message('+ Test configuration based on available test interfaces generated')
        return temp_file_path

    def _get_user_name(self):
        user_name_without_spaces = self.reservation['Username'].replace(' ', '_')
        return user_name_without_spaces

    def _message(self, message):
        self.testshell_api.WriteMessageToReservationOutput(self.reservation['ReservationId'], message)

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


def send_file(self, local_path, remote_path):
    if not self._session:
        self.connect()
    scp = SCPClient(self._session.get_handler().get_transport())
    scp.put(local_path, remote_path)