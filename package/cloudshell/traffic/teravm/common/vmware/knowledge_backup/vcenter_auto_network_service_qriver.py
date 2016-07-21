from qualipy.common.libs.driver_builder_wrapper import DriverFunction
from qualipy.virtualization.vcenter import vcenter_i18n
from qualipy.virtualization.vmware.knowledge_backup.vcenter_base_service_driver import VcenterBaseServiceDriver
from qualipy.virtualization.vcenter.vcenter_dropdown_manager import moref_from_dropdown_value, dropdownval

__author__ = 'eric.r'

class VcenterAutoNetworkServiceDriver(VcenterBaseServiceDriver):
    @DriverFunction
    def Init(self, matrixJSON):
        VcenterBaseServiceDriver.Init(self, matrixJSON)

    @DriverFunction(alias='Create', category='Administration', order='1')
    def create(self, matrixJSON):
        self.ensure_testshell(matrixJSON)

        vsphere, vcenter_attrs = self.connect_vcenter(matrixJSON)
        try:
            dvswitch_dropdown = vcenter_attrs[vcenter_i18n.DEFAULT_VIRTUAL_SWITCH_ATTR]
            if dvswitch_dropdown == 'Auto':
                dvswitch = vsphere.get_default_dvswitch()
                dvswitch_moref = dvswitch.moref
                self.testshell.write_message(self.resid, 'Using virtual switch '+dvswitch.name+' by default')
            else:
                dvswitch_moref = moref_from_dropdown_value(dvswitch_dropdown)
                self.testshell.write_message(self.resid, 'Using selected default virtual switch '+dvswitch_moref)

            vlans = self.service_attrs[vcenter_i18n.VLAN_ID_ATTR]
            vlans = vlans.strip()

            if vlans == '':
                vlans = str(vsphere.get_unused_vlan_number(dvswitch_moref))

            mode = self.service_attrs[vcenter_i18n.VLAN_MODE_ATTR]

            if mode == vcenter_i18n.VLAN_MODE_TRUNK:
                vlantype = 'VLAN Trunking'
            else:
                vlantype = 'VLAN'

            pgname = vcenter_i18n.portgroup_name(vlans=vlans,
                                                 service_name=self.service_name,
                                                 dvswitch_moref=dvswitch_moref,
                                                 user=self.testshell_user)

            pgtype = 'earlyBinding'

            self.testshell.write_message(self.resid, 'Creating portgroup '+pgname)

            def progress_handler(message, percent):
                self.testshell.write_message(self.resid, 'Creating portgroup {0}: {1}%'.format(pgname, percent))

            new_pgobj = vsphere.add_dvportgroup_to_dvswitch(dvswitch_moref, pgname, 128, pgtype, vlantype, vlans, True, progress_handler=progress_handler)

            pgdropdown = dropdownval(vcenter_attrs['name'], new_pgobj)

            # qualiapi = QualiAPIClient(self.testshell_ip, self.quali_port, self.testshell_user, self.testshell_password, self.testshell_domain)
            # vsphere.load_tree()
            # reload_all_dropdowns(qualiapi, self.testshell, vsphere, self.resid, vcenter_attrs['name'])

            self.reload_dropdowns(vcenter_attrs['name'], vsphere)

            # update_testshell_dropdowns(qualiapi, self.testshell, self.resid, vcenter_attrs['name'],
            #                            dict(map(lambda s: (s, [pgdropdown]), vcenter_i18n.network_attrs)), keep_current=True, delete_mode=False)

            self.testshell.replace_service(self.resid,
                                           self.service_name,
                                           vcenter_i18n.EXISTING_NETWORK_SERVICE_NAME,
                                           self.service_name,
                                           {
                                               vcenter_i18n.NETWORK_ATTR: pgdropdown
                                           })

            self.testshell.write_message(self.resid, 'Created portgroup '+pgdropdown)
        finally:
            vsphere.disconnect()