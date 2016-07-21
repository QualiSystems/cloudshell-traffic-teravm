import unittest
import mock
import VSphereResourceDriver
import pyVmomi
import ssl
import json

from pyVmomi import vim
from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner
from vCenterExceptions import VmWareObjectNotFoundException
import json

#+++ globally disable ssl verification by monkeypatching the ssl module in versions of Python that implement this +++#
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


class Test_vSphere_integration_tests(unittest.TestCase):
    def setUp(self):
        VSphereResourceDriver.Connect(self,"192.168.42.74","Administrator","Password1")
        #VSphereResourceDriver.Connect(self,"192.168.42.185","root","Password1")

    def tearDown(self):
        VSphereResourceDriver.Disconnect(self);

    def test_vm_power_on_when_vm_is_powered_off(self):  
        #arrange
        res = VSphereResourceDriver.PowerOff(self,"test_vm") 

        #act
        res = VSphereResourceDriver.PowerOn(self,"test_vm")      
        
        #assert
        self.assertEqual(res, "test_vm poweredOn")

    def test_vm_power_off_when_vm_is_powered_on(self):
        #arrage
        res = VSphereResourceDriver.PowerOn(self,"test_vm")

        #act
        res = VSphereResourceDriver.PowerOff(self,"test_vm")

        #assert
        self.assertEqual(res, "test_vm poweredOff")

    def test_suspend_vm(self):
        #arrage
        res = VSphereResourceDriver.PowerOn(self,"test_vm")

        #act
        res = VSphereResourceDriver.Suspend(self,"test_vm")

        #assert
        self.assertEqual(res, "test_vm suspended")

    def test_create_new_cluster(self):
        #act    
        res = VSphereResourceDriver.CreateNewCluster(self,"test cluster","HA",True,False,"manual")
        VSphereResourceDriver.DeleteCluster(self,"test cluster")

        #assert
        self.assertEqual(res,"cluster: test cluster created under: HA")
    
    def test_create_datacenter(self):
        #act
        VSphereResourceDriver.CreateDatacenter(self, "ut datacenter")
        result = VSphereResourceDriver.DeleteDatacenter(self, "ut datacenter")

        #assert
        self.assertEqual(result, "datacenter ut datacenter deleted")

    def test_set_lockdown_mode(self):
        #arrange
        VSphereResourceDriver.SetLockdownMode(self,"192.168.42.72",True)

        #act
        result = VSphereResourceDriver.SetLockdownMode(self,"192.168.42.72",False)

        #assert
        self.assertEqual(result,"Finished exiting lockdown mode succesfully. Host: 192.168.42.72")

    @unittest.skip("power tools are not installed")    
    def test_enable_remote_connections_is_success(self):
        #arrage
        VSphereResourceDriver.PowerOn(self,"test_vm")      
        #act
        res = VSphereResourceDriver.EnableRemoteConnections(self, "test_vm", "administrator", "qs@L0cal")

        #assert
        self.assertEqual(res, "Remote connections enabled successfully")

    def test_set_network_adapter_label(self):
        #act
        res = VSphereResourceDriver.SetNetworkAdapterLabel(self, "test_vm", "Network adapter 1", "VM Network 2")
        #assert
        self.assertEqual(res, "success")

    def test_mount_iso_to_cd(self):
        #act
        res = VSphereResourceDriver.MountIsoToCd(self, "DRSStorage","test_vm","ISO/test1.iso")
        #assert
        self.assertEqual(res, "success")

    def test_set_vm_startup_priority(self):
         #act
        result = VSphereResourceDriver.SetVmStartupPriority(self,"test_vm",1,-1)
        
        #assert
        self.assertEqual(result,"Successefully updated startup priority")

    def test_set_vmhost_start_policy(self):
        #arrange
        VSphereResourceDriver.SetVmhostStartPolicy(self,"192.168.42.72",True)
        
        #act
        result = VSphereResourceDriver.SetVmhostStartPolicy(self,"192.168.42.72",False)

        #assert
        self.assertEqual(result,"Successfully disabled start policy on vmhost 192.168.42.72")

    @unittest.skip("the host needs manual intervention in order to spin up")
    def test_restart_host(self):
        #act
        result = VSphereResourceDriver.RestartHost(self,"192.168.42.72",True)

        #assert
        self.assertEqual(result,"host: 192.168.42.72 rebooted")

    def test_get_hard_disks(self):
        result = VSphereResourceDriver.GetHardDisks(self,"test_vm")
        self.assertTrue(result != None)

    def test_get_available_datastores(self):
        result = VSphereResourceDriver.GetAvailableDataStores(self)
        self.assertTrue(result != None)

    def test_set_datastore_name(self):
        VSphereResourceDriver.SetDatastoreName(self,"DRSStorage","DRSStorage1")
        result = VSphereResourceDriver.SetDatastoreName(self,"DRSStorage1","DRSStorage")
        self.assertEqual(result, "DRSStorage")

    def test_set_host_start_policy_enabled(self):
        VSphereResourceDriver.SetVmhostStartPolicy(self,"192.168.42.72",False)
        result = VSphereResourceDriver.SetVmhostStartPolicy(self,"192.168.42.72",True)

        self.assertEqual(result, "Successfully enabled start policy on vmhost 192.168.42.72")
    
    def test_get_available_datasotres(self):
        result = VSphereResourceDriver.GetAvailableDataStores(self)
        obj = json.loads(result)
        self.assertIsNotNone(obj["192.168.42.72"]['DRSStorage'])

    def test_get_vmhosts(self):
        result = VSphereResourceDriver.GetVmhosts(self,"192.168.42.72","HA")
        obj = json.loads(result)

        self.assertEqual(obj[0][u'name'],"192.168.42.72")

    def test_manage_host_and_dns_routing(self):
        result = VSphereResourceDriver.ManageHostDnsAndRouting(self, "192.168.42.72",["192.168.42.3", "192.168.42.2"],"qualisystems.local","win-6tp9j31b4pg")
        self.assertEqual(result, "Successfully updated dns and rounting configurations")

    def test_set_host_advanced_parameter(self):
        result = VSphereResourceDriver.SetHostAdvancedParameter(self,"192.168.42.72","Disk.MaxResetLatency", 3000)
        self.assertEqual(result,"Successfully updated advanced parameter")

    def test_set_host_firewall(self):
        result = VSphereResourceDriver.SetHostFirwall(self, "192.168.42.72","CIM Server", False)
        VSphereResourceDriver.SetHostFirwall(self, "192.168.42.72","CIM Server", True)
        self.assertEqual(result,"Successfully updated firewall exception state")

    def test_set_host_ntp(self):
        result = VSphereResourceDriver.SetHostNTP(self, "192.168.42.72", ["il.pool.ntp.org", "0.asia.pool.ntp.org"])
        self.assertEqual(result,"Successfully updated ntp servers")

    def test_get_Exi_version(self):
        result = VSphereResourceDriver.GetEsxiVersion(self,"192.168.42.72")
        self.assertEqual(result,"6.0.0")

    def test_extend_hard_disk_capacity(self):
        #arrange
        VSphereResourceDriver.PowerOff(self, "test_vm")
        result = VSphereResourceDriver.AddHarddiskToVm(self,"192.168.42.72", "HA","DRStorage","test_vm",20,"[DRSStorage] Test VM/test_vm_test.vmdk")
        
        #act
        result = VSphereResourceDriver.ExtendHardDiskCapacity(self,"HA","[DRSStorage] Test VM/test_vm_test.vmdk",33)        
        
        #cleanup
        cleanup_result = VSphereResourceDriver.RemoveHarddiskFromVm(self,"192.168.42.72","HA","DRSStorage","test_vm","[DRSStorage] Test VM/test_vm_test.vmdk")

        #assert
        self.assertEqual("Reconfiguring [DRSStorage] Test VM/test_vm_test.vmdk complete",result)               


    def test_deploy_ovf(self):
        #arrage
        VSphereResourceDriver.DeleteVm(self, "VmFromOvf")
        #act
        res = VSphereResourceDriver.DeployOvf(self, "./test_assets/vmware/InstallationTemplate.ovf", "192.168.42.72","HA","DRSStorage","VmFromOvf")
        #assert
        self.assertEqual(res, 0)
        #cleanup
        VSphereResourceDriver.DeleteVm(self, "VmFromOvf")

    def test_delete_vm(self):
        #arrage
        VSphereResourceDriver.DeployOvf(self, "./test_assets/vmware/InstallationTemplate.ovf", "192.168.42.72","HA","DRSStorage","VmFromOvf")
        #act
        res = VSphereResourceDriver.DeleteVm(self, "VmFromOvf")
        #assert
        self.assertEqual(res, "success")
    
    def test_add_harddisk_to_vm(self):
        #arrange
        VSphereResourceDriver.PowerOff(self, "test_vm")
        #act
        result = VSphereResourceDriver.AddHarddiskToVm(self, "192.168.42.72", "HA", "DRSStorage", "test_vm", 20,"[DRSStorage] Test VM/test_vm_test.vmdk")
        #cleanup
        VSphereResourceDriver.RemoveHarddiskFromVm(self, "192.168.42.72", "HA", "DRSStorage", "test_vm","[DRSStorage] Test VM/test_vm_test.vmdk")
        #assert
        self.assertEqual(result, "success")        

    def test_remove_harddisk_from_vm(self):
        #arrange
        VSphereResourceDriver.PowerOff(self, "test_vm")
        result = VSphereResourceDriver.AddHarddiskToVm(self, "192.168.42.72", "HA", "DRSStorage", "test_vm", 20,"[DRSStorage] Test VM/test_vm_test.vmdk")
        
        #act
        result = VSphereResourceDriver.RemoveHarddiskFromVm(self,"192.168.42.72", "HA", "DRSStorage","test_vm","[DRSStorage] Test VM/test_vm_test.vmdk")

        #assert
        self.assertEqual(result,"success")
    
    @unittest.skip("power tools are not installed")    
    def test_set_vm_nic(self):
        #arrange
        VSphereResourceDriver.PowerOn(self, "test_vm")
        #act
        result = VSphereResourceDriver.SetVMNic(self, "test_vm", "administrator", "qs@L0cal", "192.168.30.250", "255.255.255.0", "192.168.30.1", "192.168.42.3", "192.168.42.2")
        #assert
        self.assertRegexpMatches(result, "IP Address configured successfully")        

    def test_set_vm(self):
        #arrange
        VSphereResourceDriver.PowerOff(self, "test_vm")
        #act
        result = VSphereResourceDriver.SetVm(self, "test_vm", "1", 4)
        #assert
        self.assertRegexpMatches(result, "Updating VM 'test_vm' \([a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}\) to 'number of CPUs':4 completed")

    def test_set_vm_advanced_parameters(self):
        #act
        result = VSphereResourceDriver.SetVmAdvancedParameters(self, "test_vm", "test_param", "test_value")
        #assert
        self.assertEqual(result, "Setting advanced parameter completed")
    
    def test_set_vm_start_policy(self):
        #arrange
        VSphereResourceDriver.PowerOff(self,"test_vm")
        #act
        result = VSphereResourceDriver.SetVmStartPolicy(self, "test_vm", 2000)
        #assert
        self.assertEqual(result, "Reconfiguring test_vm with start delay to 2000 ms completed")
        
    def test_set_vm_state_power_on_when_vm_is_power_off(self):
        #arrange
        VSphereResourceDriver.SetVmState(self, "test_vm", "powerOff")
        #act
        result = VSphereResourceDriver.SetVmState(self, "test_vm", "powerOn")
        #assert
        self.assertEqual(result, "test_vm poweredOn")

    def test_get_vm_ip(self):
        #act
        result = VSphereResourceDriver.GetVmIP(self, "test_vm")
        #assert
        self.assertRegexpMatches(result, '{"ip": .+?|None, "name": "test_vm"}')

    @unittest.skip("power tools are not installed")    
    def test_update_vm_tools(self):
        #arrage
        VSphereResourceDriver.UpdateVMTools(self, "test_vm")
        #act
        result = VSphereResourceDriver.UpdateVMTools(self, "test_vm")
        #assert
        self.assertRegexpMatches(result, "VM tools are up to date on 'test_vm' \([a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}\)")

    def test_get_vm_tools_status(self):
        #act
        result = VSphereResourceDriver.GetVMToolsStatus(self, "test_vm")
        #assert
        self.assertRegexpMatches(result, '\[\{"instanceUuid": "[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", "toolsVersionStatus": "guestTools.+"\}\]')

    def test_get_vm_guest_os(self):
        #act
        result = VSphereResourceDriver.GetVMGuestOSs(self, "test_vm")
        #assert
        obj = json.loads(result)
        self.assertIsNotNone (json.loads(result)[0][u'instanceUuid'])        

    def test_get_status(self):
        #arrage
        VSphereResourceDriver.PowerOn(self, "test_vm")
        #act
        result = VSphereResourceDriver.GetStatus(self, "test_vm")
        #assert
        obj = json.loads(result)
        self.assertIsNotNone (json.loads(result)[0]['instanceUUID'])

    def test_get_vms(self):
        #act
        result = VSphereResourceDriver.GetVms(self)
        #assert
        obj = json.loads(result)
        self.assertGreaterEqual (len(obj), 1)

    def test_manage_vswitch(self):
        #act
        result = VSphereResourceDriver.ManageVSwitch(self, "192.168.42.72", "vSwitch0", "vmnic0", 2000, 125)
        #assert
        self.assertEqual(result, "Successfully updated vSwtich configurations")

    def test_set_nic_teaming_policy(self):
        #act
        result = VSphereResourceDriver.SetNicTeamingPolicy(self, "192.168.42.72", "vSwitch0", "vmnic0", "Active")
        #assert
        self.assertEqual(result, "Configured nic teaming policy successfully")

    def test_enable_disable_vmotion(self):
        #act
        result = VSphereResourceDriver.EnableDisableVMotion(self, "192.168.42.72", "Management Network", True)
        #assert
        self.assertRegexpMatches(result, "Selected vnic .+? for vmotion")

    def test_set_teaming_inheritance(self):
        #act
        result = VSphereResourceDriver.SetTeamingInheritance(self, "192.168.42.72", "Management Network", "loadbalance_srcmac","BeaconProbing", True, False)
        #assert
        self.assertRegexpMatches(result, "set port group Management Network teaming data")

    def test_set_notify_switches(self):
        #act
        result = VSphereResourceDriver.SetNotifySwitches(self, "192.168.42.72","vSwitch0", False)
        #assert
        self.assertEqual(result, "notify switches is set to False")

    def test_enable_disable_management_trafic(self):
        #arrange
        VSphereResourceDriver.EnableDisableManagementTraffic(self, "192.168.42.72","Management Network", True)
        #act
        result = VSphereResourceDriver.EnableDisableManagementTraffic(self, "192.168.42.72","Management Network", False)
        #assert
        self.assertEqual(result, "Port group Management Network, management disabled on vmk0")

    def test_set_load_balancing_policy(self):
        #act
        result = VSphereResourceDriver.SetLoadbalancingPolicy(self, "192.168.42.72", "vSwitch0", "failover_explicit")
        #assert
        self.assertEqual(result, "Load balancing policy is set to failover_explicit")

    def test_set_network_failover_detection(self):
        #act
        result = VSphereResourceDriver.SetNetworkFailoverDetection(self, "192.168.42.72", "vSwitch0", "LinkStatus")
        #assert
        self.assertEqual(result, "Network failover detection is set to LinkStatus")

    def test_enable_disable_failback(self):
        #act
        result = VSphereResourceDriver.EnableDisableFailback(self, "192.168.42.72", "vSwitch0", False)
        #assert
        self.assertEqual(result, "Failback is disabled on vSwitch0")

    def test_remove_vm_kernel(self):
        #arrange
        result = VSphereResourceDriver.NewVirtualPortGroup(self, "192.168.42.72", "vSwitch0", "test pg")
        result = VSphereResourceDriver.AddVmKernelNetworking(self, "192.168.42.72", "test pg", "192.192.192.199","255.255.255.0", 0, True, "vSwitch0")
        #act
        result = VSphereResourceDriver.RemoveVmKernel(self, "192.168.42.72", "test pg")
        #cleanup
        VSphereResourceDriver.RemovePortGroup(self, "192.168.42.72", "test pg")
        #assert
        self.assertEqual(result, "Nic removed from test pg")

    def test_remove_vlan(self):
        #arrange
        VSphereResourceDriver.AddVlan(self, "192.168.42.72", "vSwitch0", "test pg", 0)
        #act
        result = VSphereResourceDriver.RemoveVlan(self, "192.168.42.72", "test pg")
        #assert
        self.assertEqual(result, "Removed port group test pg")

    def test_new_vmhost_net_adapter(self):
        #arrange
        result = VSphereResourceDriver.NewVirtualPortGroup(self, "192.168.42.72", "vSwitch0", "test pg")
        #act
        result = VSphereResourceDriver.NewVmhostNetAdapter(self, "192.168.42.72", "192.168.55.66", "255.255.255.0", "test pg")
        #cleanup
        VSphereResourceDriver.RemoveVmKernel(self, "192.168.42.72", "test pg")
        VSphereResourceDriver.RemovePortGroup(self, "192.168.42.72", "test pg")
        #assert
        self.assertEqual(result, "New adapter added to port group test pg")
        
    def test_new_virtual_port_group(self):
        #arrange
        VSphereResourceDriver.RemovePortGroup(self, "192.168.42.72", "test pg")
        #act
        result = VSphereResourceDriver.NewVirtualPortGroup(self, "192.168.42.72", "vSwitch0", "test pg", 0)
        #cleanup
        VSphereResourceDriver.RemovePortGroup(self, "192.168.42.72", "test pg")
        #assert
        self.assertEqual(result, "Port group test pg created on vSwitch0")        

    def test_set_maintanance_mode(self):
        #act
        result = VSphereResourceDriver.SetMaintanenceMode(self,"192.168.42.72", True)

        #assert
        self.assertEqual(result, "maintnance mode on 192.168.42.72 is now enabled")
        
        #cleanup
        result = VSphereResourceDriver.SetMaintanenceMode(self,"192.168.42.72", False)

    def test_set_persistant_scratch_location(self):
        #act
        result = VSphereResourceDriver.SetPersistentScratchLocation(self,"192.168.42.72","DRSStorage","HA")

        #assert
        self.assertTrue(result,"scratch location set to [DRSStorage] locker_1921684272")

    def test_get_vmhhost_network_adapter(self):
        
        #act
        result = VSphereResourceDriver.GetVmhostNetworkAdapters(self,"192.168.42.72",True)

        #assert
        obj = json.loads(result)
        self.assertIsNotNone(obj[0][u'mac'])
    
    def test_get_v_switch(self):
        #act
        result = VSphereResourceDriver.GetVSwitch(self,"vSwitch0","192.168.42.72")
        
        #assert
        obj = json.loads(result)
        self.assertEqual(json.loads(result)[0][u'name'], "vSwitch0")

    @unittest.skip("currently this will fail because there isn't a free nic on the server")
    def test_add_host_phyisical_adapter_to_vdswitch(self):
        #act
        result = VSphereResourceDriver.AddHostPhysicalAdapterToDvswitch(self,"192.168.42.72", "vmnic0","dvSwitch")
        
        #assert
        self.assertEqual(result,"Successfully configured dvSwitch 'dvSwitch' with pysical network adapter 'vmnic0' from host '192.168.42.72'")             

    def test_add_host_to_virtual_switch(self):
        #arrange
        VSphereResourceDriver.RemoveHostFromVirtualSwitch(self,'dvSwitch', '192.168.42.72')

        #act
        result = VSphereResourceDriver.AddHostToVirtualSwitch(self,'dvSwitch','192.168.42.72')

        #assert
        self.assertEqual(result,"Successfully added host '192.168.42.72' to dvSwitch 'dvSwitch'")

    def test_get_canonical_names(self):
        #act
        result = VSphereResourceDriver.GetCanonicalNames(self, "192.168.42.72")
        #assert
        self.assertEqual(result, '["t10.ATA_____ST500DM0022D1BD142___________________________________W3T5JK4Y", "mpx.vmhba32:C0:T0:L0"]')

    def test_add_vm_kernel_networking(self):
        #arrange
        VSphereResourceDriver.RemoveVmKernel(self,'192.168.42.72','VM Network')
    

        #act
        result = VSphereResourceDriver.AddVmKernelNetworking(self,'192.168.42.72','VM Network',"192.192.192.197","255.255.255.0", 5,True, "vSwitch0")

        #assert
        self.assertEqual(result, "done adding vm kernel networking")

    def test_upload_file_to_datastore(self):
        #arrange
        VSphereResourceDriver.DeleteFileFromDatastore(self, "192.168.42.74", "HA", "DRSStorage", "./test_assets/vmware/testdoc1.txt", False)
        #act
        result = VSphereResourceDriver.UploadFileToDatastore(self, "192.168.42.74", "HA", "DRSStorage", "./test_assets/vmware/testdoc1.txt", "testdoc1.txt", False)
        #cleanup
        VSphereResourceDriver.DeleteFileFromDatastore(self, "192.168.42.74", "HA", "DRSStorage", "./test_assets/vmware/testdoc1.txt", False)
        #assert
        self.assertRegexpMatches(result, "^Success.*")        

    @unittest.skip("currently this will fail because there isn't a free nic on the server")
    def test_add_vmkernel_to_vdswitch(self):
        #act
        result = VSphereResourceDriver.AddVmKernelToDvswitch(self,'192.168.42.72','vmk0','dvSwitch','dvPortGroup')

        #assert
        self.assertEqual(1,2)


    def test_add_vlan(self):
        #act
        result = VSphereResourceDriver.AddVlan(self,'192.168.42.72',"vSwitch0", "VM Network",3)

        #assert
        self.assertEqual(result,'vlan (id=3) added to port group VM Network')


    def test_get_virtual_port_groups(self):
        #act
        result = VSphereResourceDriver.GetVirtualPortGroups(self,'192.168.42.72')

        #assert
        obj = json.loads(result)
        self.assertIsNotNone( obj[u'VMkernel'])

    def test_get_vmk(self):
        #act
        result = VSphereResourceDriver.GetVmk(self)

        #assert
        obj = json.loads(result)
        self.assertIsNotNone( obj[0][u'name'])
        
    def test_make_nic_active(self):
        #act
        result = VSphereResourceDriver.MakeNicActive(self, '192.168.42.72','vSwitch0', 'vmnic0')

        #assert
        self.assertEqual(result,"vmnic vmnic0 is now active on vSwitch0") 

if __name__ == '__main__':
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
    

