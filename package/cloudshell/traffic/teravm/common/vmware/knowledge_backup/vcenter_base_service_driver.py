import random
import time
from qualipy.api.QualiAPIClient import QualiAPIClient
from qualipy.api.cloudshell_api_enhanced import CloudShellAPIEnhancedSession
from qualipy.virtualization.vcenter import vcenter_i18n
from qualipy.common.libs.driver_builder_wrapper import BaseServiceDriver, DriverFunction, json_loads
from qualipy.virtualization.vcenter.vcenter_dropdown_manager import reload_all_dropdowns
from qualipy.virtualization.vcenter.vcenter_library import ModernVsphereLibrary

__author__ = 'ericr'

class VcenterBaseServiceDriver(BaseServiceDriver):
    @DriverFunction
    def Init(self, matrixJSON):
        m = json_loads(matrixJSON)
        self.testshell_ip = m['connectivityInfo']['ServerAddress']
        self.quali_port = m['connectivityInfo']['QualiApiPort']
        self.testshell = None
        self.resid = None
        self.service_name = None
        self.service_attrs = {}

    def ensure_testshell(self, matrixJSON):
        m = json_loads(matrixJSON)
        if self.testshell is None:
            self.testshell_user = m['reservation'][vcenter_i18n.TESTSHELL_USERNAME_ATTR]
            self.testshell_password = m['reservation'][vcenter_i18n.TESTSHELL_PASSWORD_ATTR]
            self.testshell_domain = m['reservation'][vcenter_i18n.TESTSHELL_DOMAIN_ATTR]
            self.testshell = CloudShellAPIEnhancedSession(self.testshell_ip,
                                                         self.testshell_user,
                                                         self.testshell_password,
                                                         self.testshell_domain)
        self.resid = m['reservation']['ReservationId']
        self.service_name = m['resource']['ResourceName']
        self.service_attrs = self.testshell.get_service_attributes(self.resid, self.service_name)
        self.isscript = vcenter_i18n.IS_SCRIPT_ATTR in m['resource']
        return self.testshell

    def connect_vcenter(self, matrixJSON):
        vcenter_resource = None

        for vm in self.testshell.get_service_connections(self.resid, self.service_name):
            vmid = self.testshell.get_connected_resource(vm)
            if vmid is not None:
                vcenter_resource = vmid.split('/')[-3]
                self.testshell.write_message(self.resid, 'Service is connected to VM '+vmid+' on vCenter '+vcenter_resource)
                break

        # for conn in self.testshell.GetReservationDetails(self.resid).ReservationDescription.Connectors:
        #     vm = None
        #     if conn.Source == self.service_name:
        #         vm = conn.Target
        #     if conn.Target == self.service_name:
        #         vm = conn.Source
        #     if vm is not None:

        if vcenter_resource is None:
            for vcenter in self.testshell.FindResources(vcenter_i18n.CLOUD_PROVIDER_FAMILY, vcenter_i18n.CLOUD_PROVIDER_MODEL).Resources:
                vcenter_resource = vcenter.Name
                self.testshell.write_message(self.resid, 'Using the first vCenter in the system: '+vcenter_resource)
                break

        if vcenter_resource is None:
            raise Exception('Unable to create virtual network: No vCenter found in the system')

        self.testshell.write_message(self.resid, 'Using vCenter '+vcenter_resource)

        vcenter_attrs = self.testshell.get_resource_attributes(vcenter_resource)
        vsphere = ModernVsphereLibrary(
            vcenter_attrs['address'],
            vcenter_attrs[vcenter_i18n.VSPHERE_USER_ATTR],
            self.testshell.decrypt_resource_password(vcenter_attrs[vcenter_i18n.VSPHERE_PASSWORD_ATTR]),
            vcenter_attrs[vcenter_i18n.AUTOLOAD_FILTER_ATTR])
        return vsphere, vcenter_attrs

    def reload_dropdowns(self, vcenter_name, vsphere):
        # import uuid
        # s = self.service_name+str(uuid.uuid4())
        # self.testshell.lock_mutex(vcenter_name, vcenter_i18n.MUTEX_ATTR, s, 30)
        # try:
        qualiapi = QualiAPIClient(self.testshell_ip, self.quali_port, self.testshell_user, self.testshell_password, self.testshell_domain)
        vsphere.load_tree(lite=True)
        for i in range(0, 10):
            try:
                reload_all_dropdowns(qualiapi, self.testshell, vsphere, self.resid, vcenter_name)
                break
            except Exception as e:
                print e
            time.sleep(random.randint(1, 10))

            # finally:
            #     self.testshell.unlock_mutex(vcenter_name, vcenter_i18n.MUTEX_ATTR, s)

            # if not self.isscript:
            #     for vm in self.testshell.get_connected_root_resources(self.resid, self.service_name):
            #         if self.testshell.get_resource_attributes(vm)['model'] == vcenter_i18n.ROOT_VM_MODEL:
            #             self.testshell.write_message(self.resid, 'Executing vCenter dropdown refresh via connected VM '+vm)
            #             self.testshell.ExecuteResourceConnectedCommand(self.resid, vm, 'remote_reload_dropdowns', 'remote_reload_dropdowns', [], [], printOutput=True)
            #             return
            # self.testshell.AddResourcesToReservation(self.resid, [vcenter_name])
            # if self.isscript:
            #     self.testshell.ExecuteCommand(self.resid, vcenter_name, 0, 'VcenterAutoloadResourceDriver__reload_dropdowns', [], printOutput=True)
            # else:
            #     self.testshell.ExecuteResourceCommand(self.resid, vcenter_name, 'reload_dropdowns', [], printOutput=True)
