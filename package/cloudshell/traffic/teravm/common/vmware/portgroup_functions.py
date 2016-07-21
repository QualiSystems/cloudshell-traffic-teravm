class PortGroupFunctions:
    def add_dvportgroup_to_dvswitch(self, dvswitch_typed_moref, name, number_of_ports, portgroup_type, vlan_type, vlan_details):
        si = self.si
        typed_moref_elems = dvswitch_typed_moref.split(':')
        dvSwitch = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if dvSwitch is None:
            raise SystemExit("Unable to find dvSwitch " + dvswitch_typed_moref)
        dvSwitch._stub = si._stub
        spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
        spec.name = name
        spec.numPorts = number_of_ports
        portgroup_types = {
            "earlyBinding": vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding,
            "ephemeral": vim.dvs.DistributedVirtualPortgroup.PortgroupType.ephemeral,
            "lateBinding": vim.dvs.DistributedVirtualPortgroup.PortgroupType.lateBinding
        }
        if portgroup_type not in portgroup_types:
            raise SystemExit('Unknown portgroup type ' + portgroup_type)
        spec.type = portgroup_types[portgroup_type]
        dvsPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
        dvsVlanSpec = {
            'VLAN': vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec(),
            'VLAN Trunking' : vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec(),
            'Private VLAN': vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec()
        }
        if vlan_type not in dvsVlanSpec:
            raise SystemExit('Unknown VLAN type ' + vlan_type)
        p = re.compile("(\d+-\d+|\d+)(,(\d+-\d+|\d+))*")
        if (not p.match(vlan_details)) :
            raise SystemExit('Invalid syntax of vlan_details. Should be either integer or comma separated list of ranges')

        if vlan_type == 'VLAN':
            dvsVlanSpec[vlan_type].vlanId = int(vlan_details)
        elif(vlan_type == 'Private VLAN'):
            dvsVlanSpec[vlan_type].vlan = int(vlan_details) # TODO: figure out how to assign vlans for Private VLAN option
        elif (vlan_type == 'VLAN Trunking'):
            range_elements = vlan_details.split(',')
            numeric_ranges = []
            for range_element in range_elements:
                numeric_range = vim.NumericRange()
                try:
                    start_of_range = int(range_element.split('-')[0])
                    end_of_range = int(range_element.split('-')[1])
                except IndexError:
                    end_of_range = int(range_element)
                numeric_range.start = start_of_range
                numeric_range.end = end_of_range
                numeric_ranges.append(numeric_range)
            dvsVlanSpec[vlan_type].vlanId = numeric_ranges

        dvsPortConfig.vlan = dvsVlanSpec[vlan_type]
        spec.defaultPortConfig = dvsPortConfig
        dvSwitch.CreateDVPortgroup_Task(spec=spec)
        print "Port group " + name + " has been successfully added"
    def delete_dvportgroup_from_dvswitch(self, portgroup_typed_moref):
        si = self.si
        typed_moref_elems = portgroup_typed_moref.split(':')
        portGroup = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if portGroup is None:
            raise SystemExit("Unable to find portGroup " + portgroup_typed_moref)
        portGroup._stub = si._stub

        portGroup.Destroy_Task()
        print "Port group " + portGroup.name + " has been successfully removed"
    def get_vlans(self, dvs_moref):
        si = self.si
        typed_moref_elems = dvs_moref.split(':')
        dv_switch = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if dv_switch is None:
            raise SystemExit("Unable to find dvSwitch " + dvs_moref)
        dv_switch._stub = si._stub
        result_dict = {}
        for dvportgroup in dv_switch.portgroup:
            for vlan_number in range(1,4094):
                if (not result_dict.has_key(vlan_number)):
                    result_dict[vlan_number] = []
                config = fake_service.get_property(dvportgroup, 'config')
                vlanId = config.defaultPortConfig.vlan.vlanId
                if type(vlanId) is int:
                    if vlan_number == vlanId:
                        result_dict[vlan_number].append(('vim.dvs.DistributedVirtualPortgroup:' + dvportgroup.key, dvportgroup.config.description))
                else:
                    for numeric_range in vlanId:
                        if (vlan_number >= numeric_range.start and vlan_number <= numeric_range.end):
                            result_dict[vlan_number].append(('vim.dvs.DistributedVirtualPortgroup:' + dvportgroup.key, dvportgroup.config.description))
        return result_dict

class fake_service(object):
    def get_property(self, dvpg, propname):
        if propname == 'summary':
            return dvpg.summary
        if propname == 'config':
            return dvpg.config