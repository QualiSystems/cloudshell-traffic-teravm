import VSphere
import pyVmomi

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

def Connect(self, address, user, password):
    global _session
    _session = VSphere.VSphere(SmartConnect,Disconnect,vim,address, user, password)

def Disconnect(self):
    #del _session
    _session = None

def PowerOn(self, name):
    return _session.powerOn(name)

def PowerOff(self, name):
    return _session.powerOff(name)

def Suspend(self,name):
    return _session.suspend(name)

def CreateNewCluster(self,cluster_name,cluster_location,ha_enabed,drs_endabled, drs_automation_level):
    return _session.create_cluster(cluster_name,cluster_location,ha_enabed,drs_endabled, drs_automation_level)

def DeleteCluster(self,cluster_name):
    return _session.delete_cluster(cluster_name)

def RestartHost(self, host_name, force):
    return _session.restart_host(host_name, force)

def GetHardDisks(self,vm_name):
    return _session.get_hard_disks(vm_name)

def GetAvailableDataStores(self):
    return _session.get_available_datastores();

def SetDatastoreName(self, datastore_name, new_name):
    return _session.set_datastore_name(datastore_name,new_name)

def ExtendHardDiskCapacity(self, datacenter_name, file_path, capacityGB):
    return _session.extend_hard_disk_capacity(datacenter_name, file_path, capacityGB)

def ShrinkHardDiskCapacity(self, datacenter_name, file_path, capacityGB):
    return _session.shrink_hard_disk_capacity(datacenter_name, file_path, capacityGB)

def GetEsxiVersion(self,vi_server):
    return _session.get_esxi_version(vi_server)

def SetMaintanenceMode(self, vi_server, enable_maintenance_mode):
    return _session.set_maintenance_mode(vi_server,enable_maintenance_mode)

def SetPersistentScratchLocation(self,host_name, data_store_to_use, datacenter_name):
    return _session.set_persistent_scratch_location(host_name,data_store_to_use,datacenter_name)

def AddVlan(self,host_name, v_switch_name, port_group_name, vlan_id):
    return _session.add_vlan(host_name, v_switch_name, port_group_name, vlan_id)

def AddKernelNetworking(self, host_name, vswitch_name, ip, subnet_mask, mtu, port_group_name, vmotion_enabled, vmotion_state,vlan_id):
    return _session.add_vm_kernel_networking(host_name, vswitch_name, ip, subnet_mask, mtu, port_group_name, vmotion_enabled, vmotion_state,vlan_id)

def AddVmKernelNetworking(self, host_name, port_group_name, ip_address,subnet_mask, vlan_id,vmotion_active, v_switch_name):
    return _session.add_vmkernel_networking(host_name, port_group_name, ip_address,subnet_mask, vlan_id,vmotion_active, v_switch_name)

def GetVirtualPortGroups(self, host_name):
    return _session.get_virtual_port_groups(host_name)

def MakeNicActive(self, host_name, v_switch_name, vmnic_name):
    return _session.make_nic_active(host_name, v_switch_name, vmnic_name)

def NewVirtualPortGroup(self, host_name, v_switch_name, port_group_name, vlan_id):
    return _session.new_virtual_port_group(host_name, v_switch_name, port_group_name, vlan_id)

def CreateDatacenter(self, datacenter_name):
    return _session.create_datacenter(datacenter_name)

def DeleteDatacenter(self, datacenter_name):
    return _session.delete_datacenter(datacenter_name)

def SetLockdownMode(self, host_name, enable_lockdown = True):
    return _session.set_lockdown_mode(host_name, enable_lockdown)

def SetVmStartupPriority(self, vm_name, start_order, start_delay):
    return _session.set_vm_startup_priority(vm_name, start_order, start_delay)

def SetVmhostStartPolicy(self, host_name, enable_start_policy = True):
    return _session.set_vmhost_start_policy(host_name, enable_start_policy)

def GetVmhosts(self, vm_host_name, location):
    return _session.get_vmhosts(vm_host_name, location)

def GetVmk(self):
    return _session.get_vmk()

def GetVSwitch(self, name, vmhost):
    return _session.get_v_switch(name, vmhost)

def GetVmhostNetworkAdapters(self, vmhost, getOnlyPhysical):
    return _session.get_vmhost_network_adapters(vmhost, getOnlyPhysical)

def GetVms(self):
    return _session.get_vms()

def GetVmIP(self, vmname):
    return _session.get_vm_ip(vmname)

def SetVmState(self, vmname, state):
    return _session.set_vm_state(vmname, state)

def SetVmStartPolicy(self, vmname, start_delay):
    return _session.set_vm_start_policy(vmname, start_delay)

def RemoveVmKernel(self, host_name, port_group_name):
    return _session.remove_vm_kernel(host_name, port_group_name)

def EnableDisableFailback(self, host_name,v_switch_name, failback_enabled):
    return _session.enable_disable_failback(host_name,v_switch_name, failback_enabled)

def SetNetworkFailoverDetection(self, host_name,v_switch_name, net_failedover_detection):
    return _session.set_network_failover_detection(host_name,v_switch_name, net_failedover_detection)

def SetLoadbalancingPolicy(self, host_name,v_switch_name, load_balancing_policy):
    return _session.set_load_balancing_policy(host_name,v_switch_name, load_balancing_policy)

def EnableDisableManagementTraffic(self, host_name, port_group_name,enable_management):
    return _session.enable_disable_management_trafic(host_name, port_group_name,enable_management)

def SetNotifySwitches(self, host_name,v_switch_name, notify_switches):
    return _session.set_notify_switches(host_name,v_switch_name, notify_switches)

def SetTeamingInheritance(self, host_name, v_port_group_name,load_balancing_policy,net_failedover_detections,notify_switches,failback_enabled):
    return _session.set_teaming_inheritance(host_name, v_port_group_name,load_balancing_policy,net_failedover_detections,notify_switches,failback_enabled)    

def ManageHostDnsAndRouting(self, host_name, dns_servers, new_domain, new_virtual_network_host_name):
    return _session.manage_host_dns_and_routing(host_name, dns_servers, new_domain, new_virtual_network_host_name)

def SetHostAdvancedParameter(self, host_name, param_name, param_value):
    return _session.set_host_advanced_parameter(host_name, param_name, param_value)

def SetHostFirwall(self, host_name, firewall_exception, enable_exception):
    return _session.set_host_firwall(host_name, firewall_exception, enable_exception)

def SetHostNTP(self, host_name, ntp_servers):
    return _session.set_host_ntp( host_name, ntp_servers)

def GetStatus(self, vmname):
    return _session.get_status(vmname)

def GetVMGuestOSs(self, vmname):
    return _session.get_vm_guest_os(vmname)

def GetVMToolsStatus(self, vmname):
    return _session.get_vm_tools_status(vmname)

def UpdateVMTools(self, vmname):
    return _session.update_vm_tools(vmname)

def SetVmAdvancedParameters(self, vmname, key, value):
    return _session.set_vm_advanced_parameters(vmname, key, value)

def SetVMNic(self, vmname, vmguest_user, vmguest_pwd, ip_address, subnet_mask, gateway, dns_primary, dns_secondary):
    return _session.set_vm_nic(vmname, vmguest_user, vmguest_pwd, ip_address, subnet_mask, gateway, dns_primary, dns_secondary)    

def EnableDisableVMotion(self,host_name, v_port_group_name, enable_vmotion):
    return _session.enable_disable_vmotion(host_name, v_port_group_name, enable_vmotion)

def GetCanonicalNames(self, host_name):
    return _session.get_canonical_names(host_name)

def UploadFileToDatastore(self, vsphere_client_address, data_center_name, data_store_name,local_file, remote_file,disable_ssl_verification):
    return _session.upload_file_to_datastore(vsphere_client_address, data_center_name, data_store_name,local_file, remote_file,disable_ssl_verification)

def DeleteFileFromDatastore(self, vsphere_client_address, data_center_name, data_store_name, remote_file, disable_ssl_verification):
    return _session.delete_file_from_datastore(vsphere_client_address, data_center_name, data_store_name, remote_file, disable_ssl_verification)

def AddHarddiskToVm(self,host_name,data_center_name, storage_name, vm_name, hd_capacity_GB, disk_file_path):
    return _session.add_harddisk_to_vm(host_name,data_center_name, storage_name, vm_name, hd_capacity_GB,disk_file_path)

def RemoveHarddiskFromVm(self,host_name,data_center_name, storage_name, vm_name,disk_file_name):
    return _session.remove_harddisk_from_vm(host_name,data_center_name, storage_name, vm_name,disk_file_name)

def DeleteVm(self, vm_name):
    return _session.delete_vm(vm_name)

def DeployOvf(self, ovf_file_path, host_name, data_center_name, data_store_name, new_name):
    return _session.deploy_ovf(ovf_file_path, host_name, data_center_name, data_store_name, new_name)

def MountIsoToCd(self,datastore_name,vm_name, iso_path):
    return _session.mount_iso_to_cd(datastore_name,vm_name, iso_path)

def SetNetworkAdapterLabel(self,vm_name,network_adapter_name, network_adapter_new_label):
    return _session.set_network_adapter_label(vm_name,network_adapter_name, network_adapter_new_label)

def AddHostPhysicalAdapterToDvswitch(self, host_name, host_pysical_nic_name, dvs_name):
    return _session.add_host_physical_adapter_to_dvswitch(host_name, host_pysical_nic_name, dvs_name)

def AddHostToVirtualSwitch(self, dvs_name, host_name_toadd):
    return _session.add_host_to_virtual_switch(dvs_name, host_name_toadd)

def RemoveHostFromVirtualSwitch(self,dvs_name,host_name_to_remove):
    return _session.remove_host_from_virtual_switch(dvs_name,host_name_to_remove)

def AddVmKernelToDvswitch(self, host_name, vmk_name, dvs_name, virtual_port_group):
    return _session.add_vmkernel_to_dvswitch(host_name, vmk_name, dvs_name, virtual_port_group)

def SetNicTeamingPolicy(self, host_name, vswitch_name, pnic_name, nic_state):
    return _session.set_nic_teaming_policy(host_name, vswitch_name, pnic_name, nic_state)

def ManageVSwitch(self, host_name, vswitch_name, pnic_name, mtu, num_ports):
    return _session.manage_vswitch(host_name, vswitch_name, pnic_name, mtu, num_ports)

def EnableRemoteConnections(self, vm_name,vmguest_user,vmguest_pwd):
    return _session.enable_remote_connections(vm_name,vmguest_user,vmguest_pwd)
   
def SetVm(self, vmname, parameter, parameter_value):
    return _session.set_vm(vmname, parameter, parameter_value)

def NewVirtualPortGroup(self, host_name, v_switch_name, port_group_name, vlan_id=0):
    return _session.new_virtual_port_group(host_name, v_switch_name, port_group_name, vlan_id=0)

def RemovePortGroup(self, host_name, port_group_name):
    return _session.remove_port_group(host_name, port_group_name)

def RemoveVlan(self, host_name, port_group_name):
    return _session.remove_vlan(host_name, port_group_name)

def NewVmhostNetAdapter(self, host_name, kernel_adapter_ip, kernel_adapter_subnet_mask, portgroup_name):
    return _session.new_vmhost_net_adapter(host_name, kernel_adapter_ip, kernel_adapter_subnet_mask, portgroup_name)
 