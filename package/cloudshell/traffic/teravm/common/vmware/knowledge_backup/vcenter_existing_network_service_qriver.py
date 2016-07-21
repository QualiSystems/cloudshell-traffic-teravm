import threading

from qualipy.common.libs.driver_builder_wrapper import DriverFunction
from qualipy.virtualization.vcenter import vcenter_i18n
from qualipy.virtualization.vmware.knowledge_backup.vcenter_base_service_driver import VcenterBaseServiceDriver
from qualipy.virtualization.vcenter.vcenter_dropdown_manager import name_from_dropdown_value, moref_from_dropdown_value

__author__ = 'eric.r'

class VcenterNetworkServiceDriver(VcenterBaseServiceDriver):
    @DriverFunction
    def Init(self, matrixJSON):
        VcenterBaseServiceDriver.Init(self, matrixJSON)

    @DriverFunction(alias='Connect', category='Management', order=3)
    def connect(self, matrixJSON, target):
        self.ensure_testshell(matrixJSON)
        if self.isscript:
            return self.testshell.ExecuteCommand(self.resid, target, 0, 'VcenterVMManagementResourceDriver__connect', [self.service_name], printOutput=True).Output
        else:
            return self.testshell.execute_resource_direct_or_connected_command(self.resid, target, 'connect', [self.service_name], printOutput=True).Output

    @DriverFunction(alias='Disconnect', category='Management', order=5)
    def disconnect(self, matrixJSON, target):
        self.ensure_testshell(matrixJSON)
        if self.isscript:
            return self.testshell.ExecuteCommand(self.resid, target, 0, 'VcenterVMManagementResourceDriver__disconnect', [self.service_name], printOutput=True).Output
        else:
            return self.testshell.execute_resource_direct_or_connected_command(self.resid, target, 'disconnect', [self.service_name], printOutput=True).Output

    def do_command_on_all(self, matrixJSON, command):
        self.ensure_testshell(matrixJSON)
        threads = []

        def x(nw, errs):
            self.testshell.write_message(self.resid, 'Executing '+command+' on '+nw)
            try:
                if self.isscript:
                    o = self.testshell.ExecuteCommand(self.resid, nw, 0, 'VcenterVMManagementResourceDriver__'+command, [self.service_name], True)
                else:
                    o = self.testshell.execute_resource_direct_or_connected_command(self.resid, nw, command, [self.service_name], True)
                self.testshell.write_message(self.resid, command+' task completed: '+o.Output)
            except Exception as ex:
                ms = command+' task failed: '+ex.__class__.__name__+""": """+str(ex)
                errs.append(ms)
                self.testshell.write_message(self.resid, ms)

        class CommandThread(threading.Thread):
            def __init__(self, name1):
                threading.Thread.__init__(self)
                self.name = name1
                self.errors = []

            def run(self):
                x(self.name, self.errors)

        for name in map(lambda s: self.testshell.get_root_resource(s), self.testshell.get_service_connections(self.resid, self.service_name)):
            t = CommandThread(name)
            self.testshell.write_message(self.resid, 'Starting '+command+' thread for '+name)
            threads.append(t)
            t.start()

        errors = []
        for thread in threads:
            thread.join()
            for error in thread.errors:
                errors.append(error)
        if len(errors) > 0:
            raise Exception('\n\n '.join(errors))

    @DriverFunction(alias='Connect All', category='Management', order=4)
    def connect_all(self, matrixJSON):
        return self.do_command_on_all(matrixJSON, 'connect')

    @DriverFunction(alias='Disconnect All', category='Management', order=6)
    def disconnect_all(self, matrixJSON):
        return self.do_command_on_all(matrixJSON, 'disconnect')

    @DriverFunction(alias='Delete', category='Administration', order=99)
    def delete(self, matrixJSON):
        self.ensure_testshell(matrixJSON)

        pgdropdown = self.service_attrs[vcenter_i18n.NETWORK_ATTR]

        if vcenter_i18n.is_auto_portgroup(name_from_dropdown_value(pgdropdown)):
            vsphere, vcenter_attrs = self.connect_vcenter(matrixJSON)
            try:
                pg_moref = moref_from_dropdown_value(pgdropdown)

                def progress_handler(message, percent):
                    self.testshell.write_message(self.resid, 'Deleting portgroup {0}: {1}%'.format(pgdropdown, percent))

                vsphere.delete_dvportgroup_from_dvswitch(pg_moref, progress_handler=progress_handler)

                # qualiapi = QualiAPIClient(self.testshell_ip, self.quali_port, self.testshell_user, self.testshell_password, self.testshell_domain)
                # vsphere.load_tree()
                # reload_all_dropdowns(qualiapi, self.testshell, vsphere, self.resid, vcenter_attrs['name'])
                self.reload_dropdowns(vcenter_attrs['name'], vsphere)

                # update_testshell_dropdowns(qualiapi, self.testshell, self.resid, vcenter_attrs['name'],
                #                            dict(map(lambda s: (s, [pgdropdown]), vcenter_i18n.network_attrs)), keep_current=True, delete_mode=True)
            finally:
                vsphere.disconnect()
        else:
            raise Exception('Delete not performed for {0}: This service only deletes auto-created networks.'.format(pgdropdown))