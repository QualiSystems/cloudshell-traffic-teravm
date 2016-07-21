import VSphere as VSphere
import pyVmomi
import ssl

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

#+++ globally disable ssl verification by monkeypatching the ssl module in versions of Python that implement this +++#
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

a = VSphere.VSphere(SmartConnect, Disconnect, vim, "192.168.42.74", "Administrator", "Password1")

#a.powerOn("Windows2012-SharedDB01")

#a.powerOff("Windows2012-SharedDB01")

#a.create_cluster("new cluster name","TomDataCenter",False,False,"manual")

#a.restart_host("192.168.42.72",force=True)

#a.get_hard_disks("Windows2012-SharedDB01")

#a.get_available_datastores()

#a.set_datastore_name("datastore2", "datastore2")

#a.set_hard_disk_capacity("HA","[DRSStorage] Toms_3/Toms.vmdk",80)

#a.get_esxi_version("192.168.42.72")

#a.set_maintenance_mode("192.168.42.72",False)

#a.set_persistent_scratch_location("192.168.42.72", "DRSStorage", "HA")

#a.add_vlan("192.168.42.72", "vSwitch0", "toms pg",3)

#a.add_vmkernel_networking("192.168.42.72", "toms pg", "192.192.192.197","255.255.255.0", 5,True, "vSwitch0")

#print (a.get_virtual_port_groups("192.168.42.72"))

#a.make_nic_active("192.168.42.72","vSwitch0","vmnic0")

#a.new_virtual_port_group("192.168.42.72","vSwitch0", "mynew group",555)

#a.new_vmhost_net_adapter("192.168.42.72", "192.168.55.66","255.255.255.0", "mynew group")

#a.remove_vlan("192.168.42.72", "toms pg")

#a.remove_vm_kernel("192.168.42.72","toms pg")

#a.enable_disable_failback("192.168.42.72","vSwitch0", False)

#a.set_network_failover_detection("192.168.42.72","vSwitch0", "LinkStatus")

#a.set_load_balancing_policy("192.168.42.72","vSwitch0", "failover_explicit")

#a.enable_disable_management_trafic("192.168.42.72", "VM Network 3",False) 

#a.set_notify_switches("192.168.42.72","vSwitch0", False)

#print a.set_hard_disk_capacity("HA","[DRSStorage] Windows2012-SharedDB01/Windows2012-SharedDB01_5.vmdk",50)

#print a.get_VMK()

#print a.get_v_switch("vSwitch0", "192.168.42.72")

#print a.get_vmhost_network_adapters("192.168.42.72", False)

#print a.add_host_physical_adapter_to_dvswitch("192.168.42.72", "vmnic0", "dvSwitch2")

#print a.add_host_to_virtual_switch("dvSwitch2", "192.168.42.72")

#print a.get_vms()

#print a.get_vm_ip("Windows2012-SharedDB01")

#print a.set_vm_state("Windows2012-SharedDB01", "suspenddsd")

#print a.set_vm_start_policy("Windows2012-SharedDB01", 2000)

#print a.get_vmhosts("192.168.42.72", "HA")

#print a.create_datacenter("testDC")

#print a.set_vmhost_start_policy("192.168.42.72", False)

#print a.set_lockdown_mode("192.168.42.72", False)

#print a.set_vm_startup_priority("Windows2012-SharedDB02", 1, 5000)

#print a.manage_host_dns_and_routing("192.168.42.72", ["192.168.42.3", "192.168.42.2"], "qualisystems.local", "win-6tp9j31b4pg")

#print a.set_host_advanced_parameter("192.168.42.72", "Disk.MaxResetLatency", 3000)

#print a.set_host_firwall("192.168.42.72", "Active Directory Alls", False)

#print a.set_host_ntp("192.168.42.72", ["il.pool.ntp.org", "0.asia.pool.ntp.org"])

#print a.set_teaming_inheritance("192.168.42.72", "VM Network 3", "loadbalance_srcmac","BeaconProbing",True,False)

#a.set_teaming_inheritance("192.168.42.72", "VM Network 3", "loadbalance_srcmac","BeaconProbing",True,False)

#a.enable_disable_vmotion("192.168.42.72", "VM Network 3", True)

#print (a.get_canonical_name("192.168.42.72"))

#a.upload_file_to_datastore("192.168.42.74", "HA", "DRSStorage", "c:/testdoc.txt", "/folder/testdoc1.txt" ,False)

#print a.add_harddisk_to_vm("192.168.42.72","HA","DRSStorage","test_vm",20)

#print a.remove_harddisk_from_vm("192.168.42.72","HA","DRSStorage","test_vm")

#a.delete_vm("Toms")

#a.deploy_ovf("C:\\Users\\tom.h\\Desktop\\Toms\\Toms.ovf", "192.168.42.72","HA","DRSStorage","tomCopy")

#a.mount_iso_to_cd("DRSStorage","Toms","ISO/test1.iso")

#print a.set_teaming_inheritance("192.168.42.72", "VM Network 3", "loadbalance_srcmac","BeaconProbing",True,False)

#print a.get_status("Windows2012-SharedDB01")

#print a.get_vm_guest_os("Windows2012-SharedDB02")

#print a.get_vm_tools_status("Windows2012-SharedDB02")

#print a.update_vm_tools("Windows2012-SharedDB01")

#print a.set_vm_advanced_parameters("Toms", "bla", "bla")

#print a.set_vm("Toms", "0", 5000)

#print a.set_vm_nic("win7", "administrator", "qs@L0cal", "255.255.255.0", "192.168.42.1", "192.168.42.185", "192.168.42.3", "192.168.42.2")

#a.mount_iso_to_cd("DRSStorage","Toms","ISO/test1.iso")

#a.set_network_adapter_label("Toms","Network adapter 3","VM Network 2")

#a.enable_remote_connections("win7","administrator","qs@L0cal")

#print a.set_vm_nic("win7", "administrator", "qs@L0cal", "255.255.255.0", "192.168.42.1", "192.168.42.185", "192.168.42.3", "192.168.42.2")

#print a.add_vmkernel_to_dvswitch("192.168.42.72", "vmk0", "dvSwitch", "dvPortGroup")

#print a.set_nic_teaming_policy("192.168.42.72", "vSwitch0", "vmnic0", "Active")

#print a.manage_vswitch("192.168.42.72", "vSwitch1", "vmnic0", 2000, 24)