from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import time
import requests
import paramiko

from cloudshell.shell.core.driver_context import AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.traffic.teravm.common.vsphere_helper import get_vsphere_credentials
from cloudshell.traffic.teravm.common import i18n as c
from debug_utils import debugger


class TVMControllerHandler:
    def __init__(self):
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

    @staticmethod
    def destroy_vm_only(self, context, ports):
        # release starting_index which means I need to have it first
        # call_remote_connected
        pass


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