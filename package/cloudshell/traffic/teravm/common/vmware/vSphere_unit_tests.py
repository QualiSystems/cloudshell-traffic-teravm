import unittest
import json
import mock
import VSphere
import vSphereMocks
import VSphere
import pyVmomi
import datetime
import time

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from mock import Mock, MagicMock, create_autospec, mock_open, patch
import pyVim
from unittest.case import TestCase
import __builtin__
import object_renamer

class Test_vSphere_unit_tests(unittest.TestCase):
    def setUp(self):
        si = create_autospec(spec=vim.ServiceInstance)
        si.RetrieveContent = Mock()
        si.content = create_autospec(spec=vim.ServiceInstanceContent())
        
        mockObj= Mock()
        mockObj.SmartConnect = Mock(return_value =si)
        mockObj.Disconnect = Mock()
        
        self.session = VSphere.VSphere( mockObj.SmartConnect,mockObj.Disconnect,vim,"", "", "")        

    def tearDown(self):
        pass

    def test_power_on_when_vm_is_shut_down(self):
        #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.PowerOn = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.powerOn("test_vm") 

        #assert
        vm.PowerOn.assert_called_with()
        self.assertEqual(result,"test_vm poweredOn")
                
    def test_power_on_when_vm_is_turned_on(self):
        #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime.powerState = 'poweredOn'
        vm.PowerOn = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.powerOn("test_vm") 

        #assert
        self.assertFalse(vm.PowerOn.called)
        self.assertEqual(result,"test_vm already poweredOn")      

    def test_power_on_when_call_fails(self):
        #arrange
        task = vSphereMocks.get_error_task("mock message")
        vm = create_autospec(vim.VirtualMachine)        
        vm.PowerOn = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.powerOn("test_vm") 

        #assert
        vm.PowerOn.assert_called_with()
        self.assertEqual(result,"error powering on test_vm error:mock message")

    def test_power_on_when_exception_is_thrown(self):
        #arrange
        task = vSphereMocks.get_error_task("mock message")
        vm = create_autospec(vim.VirtualMachine)        
        vm.PowerOn = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm,side_effect= Exception("mock exception"))
        
        #act
        result = self.session.powerOn("test_vm") 

        #assert        
        self.assertEqual(result,"mock exception")


    def test_power_off_when_vm_is_turned_on(self):
        #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime.powerState = 'poweredOn'
        vm.PowerOff = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.powerOff("test_vm") 

        #assert
        vm.PowerOff.assert_called_with()
        self.assertEqual(result,"test_vm poweredOff")  

    def test_power_off_when_vm_is_shut_down(self):
         #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime.powerState = 'poweredOff'
        vm.PowerOff = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.powerOff("test_vm") 

        #assert        
        self.assertFalse(vm.PowerOff.called)
        self.assertEqual(result,"test_vm already poweredOff")  

    def test_power_off_when_call_fails(self):
         #arrange
        task = vSphereMocks.get_error_task("mock error")
        vm = create_autospec(vim.VirtualMachine)
        vm.PowerOff = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.powerOff("test_vm") 

        #assert        
        self.assertTrue(vm.PowerOff.called)
        self.assertEqual(result,"error powering off test_vm error:mock error")  

    def test_power_off_when_exception_is_thrown(self):
        #arrange
        task = vSphereMocks.get_error_task("mock message")
        vm = create_autospec(vim.VirtualMachine)        
        vm.PowerOff = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm,side_effect= Exception("mock exception"))
        
        #act
        result = self.session.powerOff("test_vm") 

        #assert        
        self.assertEqual(result,"mock exception")


    def test_suspend_when_vm_is_turned_on(self):
        #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.name = "test_vm"
        vm.runtime.powerState = 'poweredOn'
        vm.Suspend = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.suspend("test_vm") 

        #assert
        vm.Suspend.assert_called_with()
        self.assertEqual(result,"test_vm suspended")  

    def test_suspend_when_vm_is_shut_down(self):
         #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.name = "test_vm"
        vm.runtime.powerState = 'poweredOff'
        vm.Suspend = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.suspend("test_vm") 

        #assert        
        self.assertFalse(vm.Suspend.called)
        self.assertEqual(result,"test_vm powered off")
        
    def test_suspend_when_vm_is_suspended(self):
        #arrange
        task = vSphereMocks.get_success_task()
        vm = create_autospec(vim.VirtualMachine)
        vm.name = "test_vm"
        vm.runtime.powerState = 'suspended'
        vm.Suspend = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.suspend("test_vm") 

        #assert        
        self.assertFalse(vm.Suspend.called)
        self.assertEqual(result,"test_vm already suspended")  

    def test_suspend_when_call_fails(self):
         #arrange
        task = vSphereMocks.get_error_task("mock error")
        vm = create_autospec(vim.VirtualMachine)
        vm.Suspend = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm)
        
        #act
        result = self.session.suspend("test_vm") 

        #assert        
        self.assertTrue(vm.Suspend.called)
        self.assertEqual(result,"error suspending test_vm error:mock error")  

    def test_suspend_when_exception_is_thrown(self):
        #arrange
        task = vSphereMocks.get_error_task("mock message")
        vm = create_autospec(vim.VirtualMachine)        
        vm.Suspend = Mock(return_value = task)
        self.session.try_get_obj = Mock(return_value = vm,side_effect= Exception("mock exception"))
        
        #act
        result = self.session.suspend("test_vm") 

        #assert        
        self.assertEqual(result,"mock exception")


    def test_create_cluster(self):
        #arrange
        datacenter = create_autospec(vim.Datacenter)
        cluster = create_autospec( vim.ClusterComputeResource)
        datacenter.hostFolder.CreateClusterEx = Mock(return_value =cluster)
        self.session.try_get_obj = Mock(return_value = datacenter)
        
        #act
        result = self.session.create_cluster("test_cluster","HA",True,True,"manual") 

        #assert        
        call_args = datacenter.hostFolder.CreateClusterEx.call_args
        spec = call_args[1]['spec']
        self.assertTrue(spec.dasConfig.enabled)
        self.assertTrue(spec.drsConfig.enabled)
        self.assertEqual(spec.drsConfig.defaultVmBehavior,"manual")
        self.assertEqual(result, "cluster: test_cluster created under: HA")

    def test_create_cluster_with_exception(self):
        #arrange
        datacenter = create_autospec(vim.Datacenter)
        cluster = create_autospec( vim.ClusterComputeResource)
        datacenter.hostFolder.CreateClusterEx = Mock(return_value =cluster)
        self.session.try_get_obj = Mock(side_effect=Exception("mock exception"))

        #act
        result = self.session.create_cluster("test_cluster","HA",True,True,"manual") 

        #assert
        self.assertEquals(result,"mock exception")

    def test_delete_cluster(self):
        #arrange
        cluster = create_autospec( vim.ClusterComputeResource)
        self.session.try_get_obj = Mock(return_value = cluster)
        
        #act
        result = self.session.delete_cluster("test_cluster") 

        #assert        
        self.assertTrue(cluster.Destroy.called)
        self.assertEqual(result, "cluster test_cluster deleted")

    def test_delete_cluster_with_exception(self):
        #arrange
        cluster = create_autospec( vim.ClusterComputeResource)
        self.session.try_get_obj = Mock(return_value = cluster,side_effect=Exception("mock exception"))
        
        #act
        result = self.session.delete_cluster("test_cluster") 

        #assert        
        self.assertFalse(cluster.Destroy.called)
        self.assertEqual(result, "mock exception")


    def test_create_datacenter(self):
        #arramge
        rootFolder = self.session.si.content.rootFolder
        rootFolder.CreateDatacenter = Mock()

        #act
        result = self.session.create_datacenter("new_datacenter")

        #assert
        rootFolder.CreateDatacenter.assert_called_with(name ="new_datacenter")
        self.assertEqual(result, "Created datacenter 'new_datacenter' succesfully")
    
    def test_create_datacenter_with_long_name(self):
        #arramge
        rootFolder = self.session.si.content.rootFolder
        rootFolder.CreateDatacenter = Mock()

        #act
        result = self.session.create_datacenter("new_datacenternew_datacenternew_datacenternew_datacenternew_datacenternew_datacenternew_datacenternew_datacenternew_datacenternew_datacenter")

        #assert
        self.assertFalse(rootFolder.CreateDatacenter.called)
        self.assertEqual(result, "The name of the datacenter must be under 80 characters.")

    def test_create_datacenter_with_exception(self):
        #arramge
        rootFolder = self.session.si.content.rootFolder
        rootFolder.CreateDatacenter = Mock(side_effect=Exception("mock exception"))

        #act
        result = self.session.create_datacenter("new_datacenter")

        #assert
        self.assertTrue(rootFolder.CreateDatacenter.called)
        self.assertEqual(result, "mock exception")


    def test_set_lockdown_mode_host_cannot_be_found(self):
        #arrange
        vSphereMocks.set_search(self, None)
        
        #act
        result = self.session.set_maintenance_mode("non existant host",True)

        #assert
        self.assertEqual(result, "could not find host non existant host")

    def test_set_lockdown_mode_enabled_when_admin_is_disabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test host")        
        host.config.adminDisabled = True
        host.EnterLockdownMode = Mock()

        #act
        result = self.session.set_lockdown_mode("test host",True)

        #assert
        self.assertFalse(host.EnterLockdownMode.called)
        self.assertEqual(result, "Lockdown mode is already enabled, nothing to do. Host: test host")

    def test_set_lockdown_mode_enabled_when_admin_is_enabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test host")        
        host.config.adminDisabled = False
        host.EnterLockdownMode = Mock()

        #act
        result = self.session.set_lockdown_mode("test host",True)

        #assert
        self.assertTrue(host.EnterLockdownMode.called)
        self.assertEqual(result, "Failed enabling lockdown mode. Host: test host")

    def test_set_lockdown_mode_disabled_when_admin_is_disabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test host")        
        host.config.adminDisabled = True

        host.ExitLockdownMode = Mock()
        def side_effect(*args, **kwargs):
            host.config.adminDisabled = False
        host.ExitLockdownMode.side_effect = side_effect

        #act
        result = self.session.set_lockdown_mode("test host",False)

        #assert
        self.assertTrue(host.ExitLockdownMode.called)
        self.assertEqual(result, "Finished exiting lockdown mode succesfully. Host: test host")

    def test_set_lockdown_mode_disabled_when_admin_is_disabled_but_call_fails(self):
        #arrange
        host = vSphereMocks.set_search(self, "test host")        
        host.config.adminDisabled = True

        host.ExitLockdownMode = Mock()
        def side_effect(*args, **kwargs):
            host.config.adminDisabled = True
        host.ExitLockdownMode.side_effect = side_effect

        #act
        result = self.session.set_lockdown_mode("test host",False)

        #assert
        self.assertTrue(host.ExitLockdownMode.called)
        self.assertEqual(result, "Failed exiting lockdown mode. Host: test host")

    def test_set_lockdown_mode_disabled_when_admin_is_enabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test host")        
        host.config.adminDisabled = False

        host.ExitLockdownMode = Mock()        

        #act
        result = self.session.set_lockdown_mode("test host",False)

        #assert
        self.assertFalse(host.ExitLockdownMode.called)
        self.assertEqual(result, "Lockdown mode is already disabled, nothing to do. Host: test host")

    def test_set_lockdown_mode_exception(self):
        #arrange
        host = vSphereMocks.set_search(self, "test host",Exception("mock exception"))        
        host.config.adminDisabled = False

        host.ExitLockdownMode = Mock()        

        #act
        result = self.session.set_lockdown_mode("test host",False)

        #assert
        self.assertFalse(host.ExitLockdownMode.called)
        self.assertEqual(result, "mock exception")


    def test_set_vm_startup_priority_add_priority(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.summary.runtime.host.configManager.autoStartManager.Reconfigure = Mock()
        self.session.get_obj_all_byname = Mock(return_value = [vm])
        
        #act
        result = self.session.set_vm_startup_priority("test",1,1)

        #assert
        call_args = vm.summary.runtime.host.configManager.autoStartManager.Reconfigure.call_args
        power_info = call_args[1]['spec'].powerInfo[0]
        self.assertEqual(power_info.startOrder, 1);
        self.assertEqual(power_info.startDelay, 1);
        self.assertEqual(power_info.startAction, "powerOn");
        self.assertTrue(self.session.get_obj_all_byname.called)
        self.assertTrue(result,"Successefully updated startup priority")

    def test_set_vm_startup_priority_remove_priority(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.summary.runtime.host.configManager.autoStartManager.Reconfigure = Mock()
        self.session.get_obj_all_byname = Mock(return_value = [vm])
        
        #act
        result = self.session.set_vm_startup_priority("test",-1,1)

        #assert
        call_args = vm.summary.runtime.host.configManager.autoStartManager.Reconfigure.call_args
        power_info = call_args[1]['spec'].powerInfo[0]
        self.assertEqual(power_info.startOrder, -1);
        self.assertEqual(power_info.startDelay, 1);
        self.assertEqual(power_info.startAction, "none");
        self.assertEqual(power_info.stopAction, "none");
        self.assertTrue(self.session.get_obj_all_byname.called)
        self.assertTrue(result,"Successefully updated startup priority")

    def test_set_vm_startup_priority_exception(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.summary.runtime.host.configManager.autoStartManager.Reconfigure = Mock()
        self.session.get_obj_all_byname = Mock(return_value = [vm], side_effect = Exception("mock exception"))
        
        #act
        result = self.session.set_vm_startup_priority("test",-1,1)

        #assert
        self.assertTrue(self.session.get_obj_all_byname.called)
        self.assertFalse(vm.summary.runtime.host.configManager.autoStartManager.Reconfigure.called)
        self.assertTrue(result,"mock exception")


    def test_enable_remote_connections_when_success(self):  
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.guest.toolsStatus = 'toolsRunning'
        self.session.get_obj = Mock(return_value = vm)
        vSphereMocks.set_start_program_in_guest(self)
        vSphereMocks.set_list_processes_success(self)
        
        #act
        result = self.session.enable_remote_connections("test_vm", "vmguest_user", "vmguest_pass")

        #assert
        self.assertEqual(result,"Remote connections enabled successfully")  

    def test_enable_remote_connections_when_call_fail(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.guest.toolsStatus = 'toolsRunning'
        self.session.get_obj = Mock(return_value = vm)
        vSphereMocks.set_start_program_in_guest(self)
        vSphereMocks.set_list_processes_success(self)
        
        #act
        result = self.session.enable_remote_connections("test_vm", "vmguest_user", "vmguest_pass")

        #assert
        self.assertEqual(result,"Failed to enable remote connections")  

    def test_enable_remote_connections_when_command_execute_exception(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.guest.toolsStatus = 'toolsRunning'
        vSphereMocks.set_list_processes_success(self)
        mock_exc_msg = "mock exception"
        self.session.content.guestOperationsManager.processManager.StartProgramInGuest = Mock(side_effect= Exception(mock_exc_msg))
        
        #act
        result = self.session.enable_remote_connections("test_vm", "vmguest_user", "vmguest_pass")

        #assert
        self.assertEqual(result, mock_exc_msg)


    def test_set_network_adapter_label_when_call_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.config = Mock()
        vm.config.hardware = Mock()        
        self.session.get_obj = Mock(return_value = vm)
        device = create_autospec(vim.vm.device.VirtualDevice)
        device.deviceInfo = Mock()
        network_adapter_name = "vnic1"
        device.deviceInfo.label = network_adapter_name
        device.backing = Mock()
        device.backing.deviceName = network_adapter_name
        vm.config.hardware.device = [device]
        task = vSphereMocks.get_success_task()
        vm.Reconfigure = Mock(return_value = task)
        
        #act
        result = self.session.set_network_adapter_label("test_vm", network_adapter_name, "vnic2")

        #assert
        self.assertTrue(vm.Reconfigure.called)
        self.assertEqual(result,"success")  

    def test_set_network_adapter_label_when_call_fail(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.config = Mock()
        vm.config.hardware = Mock()        
        self.session.get_obj = Mock(return_value = vm)
        device = create_autospec(vim.vm.device.VirtualDevice)
        device.deviceInfo = Mock()
        network_adapter_name = "vnic1"
        device.deviceInfo.label = network_adapter_name
        device.backing = Mock()
        device.backing.deviceName = network_adapter_name
        vm.config.hardware.device = [device]
        err_msg = "failed to reconfigure"
        task = vSphereMocks.get_error_task(err_msg)
        vm.Reconfigure = Mock(return_value = task)
        
        #act
        result = self.session.set_network_adapter_label("test_vm", network_adapter_name, "vnic2")

        #assert
        self.assertTrue(vm.Reconfigure.called)
        self.assertEqual(result, err_msg)  

    def test_set_network_adapter_label_when_exception_is_thrown(self):
        #arrange     
        exc_msg = "mock exception"
        self.session.get_obj = Mock(side_effect= Exception(exc_msg))       
        
        #act
        result = self.session.set_network_adapter_label("test_vm", "vnic1", "vnic2")

        #assert
        self.assertEqual(result, exc_msg)  


    def test_mount_iso_to_cd_when_call_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.config = Mock()
        vm.config.hardware = Mock()      
          
        vcd = create_autospec(vim.vm.device.VirtualCdrom)
        vcd.key = 1
        vcd.controllerKey = 2
        vm.config.hardware.device = [vcd]

        task = vSphereMocks.get_success_task()
        vm.Reconfigure = Mock(return_value = task)
        
        self.session.get_obj = Mock(return_value = vm)
                

        #act
        result = self.session.mount_iso_to_cd("test_ds", "test_vm", "ISO/test1.iso")

        #assert
        self.assertTrue(vm.Reconfigure.called)
        self.assertEqual(result,"success")  

    def test_mount_iso_to_cd_when_call_fails(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.config = Mock()
        vm.config.hardware = Mock()      
          
        vcd = create_autospec(vim.vm.device.VirtualCdrom)
        vcd.key = 1
        vcd.controllerKey = 2
        vm.config.hardware.device = [vcd]

        task = vSphereMocks.get_error_task("error mount iso to cd")
        vm.Reconfigure = Mock(return_value = task)
        
        self.session.get_obj = Mock(return_value = vm)

        #act
        result = self.session.mount_iso_to_cd("test_ds", "test_vm", "ISO/test1.iso")

        #assert
        self.assertTrue(vm.Reconfigure.called)
        self.assertEqual(result,"error mount iso to cd")  

    def test_mount_iso_to_cd_when_exception_is_thrown(self):
        #arrange     
        exc_msg = "mock exception"
        self.session.get_obj = Mock(side_effect= Exception(exc_msg))       
        
        #act
        result = self.session.mount_iso_to_cd("test_ds", "test_vm", "ISO/test1.iso")

        #assert
        self.assertEqual(result, exc_msg)  


    def test_deploy_ovf_when_call_success(self):
        #arrange  
        def getObjByContext(*args, **kwargs):
            if args[0][0] is vim.Datacenter:
                lease = create_autospec(vim.HttpNfcLease)
                lease.state = vim.HttpNfcLease.State.ready

                lease.HttpNfcLeaseComplete = Mock()
                def onLeaseComplete(*args, **kwargs):
                    lease.state = vim.HttpNfcLease.State.done
                lease.HttpNfcLeaseComplete.side_effect = onLeaseComplete

                resourcePool = create_autospec(vim.ResourcePool)
                resourcePool.ImportVApp = Mock(return_value = lease)
                
                entity = create_autospec(vim.ManagedEntity)
                entity.resourcePool = resourcePool

                dc = create_autospec(vim.Datacenter)
                dc.hostFolder = Mock()
                dc.hostFolder.childEntity = [entity]

                return dc
            elif args[0][0] is vim.Datastore:
                return create_autospec(vim.Datastore)
            else:
                None

        self.session.get_obj = Mock(side_effect = getObjByContext)

        host = create_autospec(vim.HostSystem)
        self.session.content.searchIndex.FindByDnsName(return_value = host)

        with patch('time.sleep', return_value=None):
            with patch.object(__builtin__, 'open', mock_open(read_data=Mock()), create=True):
                #act
                result = self.session.deploy_ovf("ovf", "192.168.42.72","HA","DRSStorage","new")

        #assert
        self.assertEqual(result, 0)  
        
    def test_deploy_ovf_when_call_fail(self):
        #arrange  
        def getObjByContext(*args, **kwargs):
            if args[0][0] is vim.Datacenter:
                lease = create_autospec(vim.HttpNfcLease)
                lease.state = vim.HttpNfcLease.State.error

                resourcePool = create_autospec(vim.ResourcePool)
                resourcePool.ImportVApp = Mock(return_value = lease)
                
                entity = create_autospec(vim.ManagedEntity)
                entity.resourcePool = resourcePool

                dc = create_autospec(vim.Datacenter)
                dc.hostFolder = Mock()
                dc.hostFolder.childEntity = [entity]

                return dc
            elif args[0][0] is vim.Datastore:
                return create_autospec(vim.Datastore)
            else:
                None

        self.session.get_obj = Mock(side_effect = getObjByContext)

        host = create_autospec(vim.HostSystem)
        self.session.content.searchIndex.FindByDnsName(return_value = host)

        with patch.object(__builtin__, 'open', mock_open(read_data=Mock()), create=True):
            #act
            result = self.session.deploy_ovf("ovf", "192.168.42.72","HA","DRSStorage","new")

        #assert
        self.assertEqual(result, "error with lease state, check vcenter logs")          

    def test_deploy_ovf_when_exception_is_thrown(self):
        #arrange  
        exc_msg = "mock exception"
        self.session.content.searchIndex.FindByDnsName = Mock(side_effect = Exception(exc_msg))

        with patch.object(__builtin__, 'open', mock_open(read_data=Mock()), create=True):
            #act
            result = self.session.deploy_ovf("ovf", "192.168.42.72","HA","DRSStorage","new")

        #assert
        self.assertEqual(result, exc_msg)             

    def test_set_vmhost_start_policy_enable_when_posicy_is_initially_disabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test_host")
        host.configManager.autoStartManager.config.defaults.enabled = False
        host.configManager.autoStartManager.Reconfigure = Mock();
        
        #act
        result = self.session.set_vmhost_start_policy("test_host",True)

        #assert
        self.assertEqual("Successfully enabled start policy on vmhost test_host",result)
        self.assertTrue(host.configManager.autoStartManager.Reconfigure.called) 

    def test_set_vmhost_start_policy_enable_when_posicy_is_initially_enabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test_host")
        host.configManager.autoStartManager.config.defaults.enabled = True
        host.configManager.autoStartManager.Reconfigure = Mock();
        
        #act
        result = self.session.set_vmhost_start_policy("test_host",True)

        #assert
        self.assertEqual("Start policy on vmhost test_host is already enabled",result)
        self.assertFalse(host.configManager.autoStartManager.Reconfigure.called) 

    def test_set_vmhost_start_policy_disable_when_posicy_is_initially_enabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test_host")
        host.configManager.autoStartManager.config.defaults.enabled = True
        host.configManager.autoStartManager.Reconfigure = Mock();
        
        #act
        result = self.session.set_vmhost_start_policy("test_host",False)

        #assert
        self.assertEqual("Successfully disabled start policy on vmhost test_host",result)
        self.assertTrue(host.configManager.autoStartManager.Reconfigure.called) 

    def test_set_vmhost_start_policy_disable_when_posicy_is_initially_disabled(self):
        #arrange
        host = vSphereMocks.set_search(self, "test_host")
        host.configManager.autoStartManager.config.defaults.enabled = False
        host.configManager.autoStartManager.Reconfigure = Mock();
        
        #act
        result = self.session.set_vmhost_start_policy("test_host",False)

        #assert
        self.assertEqual("Start policy on vmhost test_host is already disabled",result)
        self.assertFalse(host.configManager.autoStartManager.Reconfigure.called)
        
    def test_set_vmhost_start_policy_exception(self):
        #arrange
        host = vSphereMocks.set_search(self, "test_host")
        host.configManager.autoStartManager.config.defaults.enabled = True
        host.configManager.autoStartManager.Reconfigure = Mock(side_effect=Exception("mock exception"))
        
        #act
        result = self.session.set_vmhost_start_policy("test_host",False)

        #assert
        self.assertEqual("mock exception",result)        

    def test_restart_host_when_host_power_state_is_known(self):
        #arrange
        host = create_autospec(vim.HostSystem)
        host.runtime.powerState = "poweredOn"
        host.Reboot = Mock()
        host.name = "test_host"
        self.session.get_obj = Mock(return_value=host)

        #act
        result = self.session.restart_host("test_host", True)
        host.runtime.powerState = "poweredOff"
        result = self.session.restart_host("test_host", True)

        #assert
        host.Reboot.assert_called_with(True)
        self.assertEqual(result, "host: test_host rebooted")

    def test_restart_host_when_host_power_state_is_not_known(self):
        #arrange
        host = create_autospec(vim.HostSystem)
        host.runtime.powerState = "papaWasARollingStone"
        host.Reboot = Mock()
        host.name = "test_host"
        self.session.get_obj = Mock(return_value=host)

        #act
        result = self.session.restart_host("test_host", True)

        #assert
        self.assertFalse(host.Reboot.called)
        self.assertEqual(result, "host: test_host power state is unknown, taking no action")

    def test_restart_host_exception(self):
        #arrange
        host = create_autospec(vim.HostSystem)
        host.runtime.powerState = "poweredOff"
        host.Reboot = Mock(side_effect = Exception("mock exception"))
        host.name = "test_host"
        self.session.get_obj = Mock(return_value=host)

        #act
        result = self.session.restart_host("test_host", True)

        #assert
        self.assertTrue(host.Reboot.called)
        self.assertEqual(result, "mock exception")


    def test_get_hard_disks(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vcontroller = create_autospec(vim.vm.device.VirtualController());
        disk = create_autospec(vim.vm.device.VirtualDisk())
        attrs = {'backing.fileName':'test',
                 'diskObjectId':'test',
                 'deviceInfo.label':'test',
                 'capacityInBytes' : 'test'}

        disk.configure_mock(**attrs)
        vm.config.hardware.device = [disk, vcontroller]
        self.session.get_obj = Mock(return_value = vm)

        #act
        result = self.session.get_hard_disks("test_vm")

        #assert
        self.assertEqual('[{"diskObjectId": "test", "label": "test", "capacityInBytes": "test", "fileName": "test"}]',result)

    def test_get_hard_disks_with_exception(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        disk = create_autospec(vim.vm.device.VirtualDisk())
        attrs = {'backing.fileName':'test',
                 'diskObjectId':'test',
                 'deviceInfo.label':'test',
                 'capacityInBytes' : 'test'}

        disk.configure_mock(**attrs)
        vm.config.hardware.device = [disk]
        self.session.get_obj = Mock(return_value = vm, side_effect=Exception("mock exception"))

        #act
        result = self.session.get_hard_disks("test_vm")

        #assert
        self.assertEqual('mock exception',result)


    def test_get_available_datastores(self):
        #arrange
        partition = vim.host.ScsiDisk.Partition()
        partition.diskName = "disk_partition_name"
        hosts =create_autospec(spec=vim.view.ContainerView)
        host1 =create_autospec(vim.HostSystem)
        host1.name="host1"
        host1_storage = host1.configManager.storageSystem;
        host1_storage_mountInfo = Mock(spec = host1_storage.fileSystemVolumeInfo.mountInfo)
        host1_storage_mountInfo.volume =Mock()
        host1_storage_mountInfo.volume.name="volume_name"
        host1_storage_mountInfo.volume.version =1
        host1_storage_mountInfo.volume.type="VMFS"
        host1_storage_mountInfo.volume.uuid = 'test'
        host1_storage_mountInfo.volume.capacity = 'test'
        host1_storage_mountInfo.volume.local = 'test'
        host1_storage_mountInfo.volume.ssd = 'test'
        host1_storage_mountInfo.volume.extent = [partition]
        host1_storage.fileSystemVolumeInfo.mountInfo = [host1_storage_mountInfo]

        host2 =create_autospec (vim.HostSystem)
        host2.name="host2"
        hosts.view =[host1,host2]

        self.session.content.viewManager.CreateContainerView = Mock(return_value = hosts)
        
        #act
        result = self.session.get_available_datastores();

        #assert
        self.assertTrue(result,'{"host2": {}, "host1": {"volume_name": {"capacity": "test", "uuid": "test", "vmfs_version": 1, "ssd": "test", "extents": ["disk_partition_name"], "local": "test"}}}')
        self.assertTrue(self.session.content.viewManager.CreateContainerView.called)

    def test_get_available_datastores_with_exception(self):
        #arrange
        partition = vim.host.ScsiDisk.Partition()
        partition.diskName = "disk_partition_name"
        hosts =create_autospec(spec=vim.view.ContainerView)
        host1 =create_autospec(vim.HostSystem)
        host1.name="host1"
        host1_storage = host1.configManager.storageSystem;
        host1_storage_mountInfo = Mock(spec = host1_storage.fileSystemVolumeInfo.mountInfo)
        host1_storage_mountInfo.volume =Mock()
        host1_storage_mountInfo.volume.name="volume_name"
        host1_storage_mountInfo.volume.version =1
        host1_storage_mountInfo.volume.type="VMFS"
        host1_storage_mountInfo.volume.uuid = 'test'
        host1_storage_mountInfo.volume.capacity = 'test'
        host1_storage_mountInfo.volume.local = 'test'
        host1_storage_mountInfo.volume.ssd = 'test'
        host1_storage_mountInfo.volume.extent = [partition]
        host1_storage.fileSystemVolumeInfo.mountInfo = [host1_storage_mountInfo]

        host2 =create_autospec (vim.HostSystem)
        host2.name="host2"
        hosts.view =[host1,host2]

        self.session.content.viewManager.CreateContainerView = Mock(return_value = hosts, side_effect=Exception("mock exception"))
        
        #act
        result = self.session.get_available_datastores();

        #assert
        self.assertTrue(result,"mock exception")        


    def test_set_hard_disk_capacity(self):
        #arrange
        success_task = vSphereMocks.get_success_task()
        datacenter =vim.Datacenter("")
        self.session.si.content.virtualDiskManager.ExtendVirtualDisk = Mock(return_value = success_task)
        self.session.get_obj = Mock(return_value=datacenter)
        #act
        result = self.session.set_hard_disk_capacity("HA","/path_to_file",12)

        #assert
        size_kb = 12*1024*1024
        self.session.si.content.virtualDiskManager.ExtendVirtualDisk.assert_called_with('/path_to_file', datacenter, size_kb, False)
        self.assertEqual(result,"reconfiguring /path_to_file complete")

    def test_set_hard_disk_capacity_task_failed(self):
        #arrange
        failed_task = vSphereMocks.get_error_task("mock task failed")
        datacenter =vim.Datacenter("")
        self.session.si.content.virtualDiskManager.ExtendVirtualDisk = Mock(return_value = failed_task)
        self.session.get_obj = Mock(return_value=datacenter)
        #act
        result = self.session.set_hard_disk_capacity("HA","/path_to_file",12)

        #assert
        size_kb = 12*1024*1024
        self.session.si.content.virtualDiskManager.ExtendVirtualDisk.assert_called_with('/path_to_file', datacenter, size_kb, False)
        self.assertEqual(result,"error reconfiguring /path_to_file. mock task failed")

    def test_set_hard_disk_capacity_exception(self):
        #arrange
        success_task = vSphereMocks.get_success_task()
        datacenter =vim.Datacenter("")
        self.session.si.content.virtualDiskManager.ExtendVirtualDisk = Mock(return_value = success_task)
        self.session.get_obj = Mock(return_value=datacenter, side_effect=Exception("mock exception"))

        #act
        result = self.session.set_hard_disk_capacity("HA","/path_to_file",12)

        #assert       
        self.assertEqual(result,"mock exception")

    def test_delete_vm_in_state_poweredoff_is_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime = Mock()
        vm.runtime.powerState = "poweredOff"
        vm.Destroy = Mock(return_value = vSphereMocks.get_success_task())
        self.session.get_obj = Mock(return_value = vm)

        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertTrue(vm.Destroy.called)
        self.assertEqual(result, "success")

    def test_delete_vm_in_state_poweredon_is_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime = Mock()
        vm.runtime.powerState = "poweredOn"
        vm.Destroy = Mock(return_value = vSphereMocks.get_success_task())
        vm.PowerOff = Mock(return_value = vSphereMocks.get_success_task())
        self.session.get_obj = Mock(return_value = vm)


    def test_delete_vm_when_vm_not_found(self):
        #arrange
        self.session.get_obj = Mock(return_value = None)

        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertEqual(result, "cannot find vm test_vm")

    def test_delete_vm_with_exception(self):
        #arrange
        self.session.get_obj = Mock(side_effect=Exception("mock exception"))
        
        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertEqual(result, 'mock exception')

    def test_add_harddisk_to_vm_is_success(self):
        #arrange
        self.session.get_obj = Mock(side_effect=Exception("mock exception"))
        #a.add_harddisk_to_vm("192.168.42.72","HA","DRSStorage","Toms",20)
        
        #act
        result = self.session.add_harddisk_to_vm("192.168.42.72", "HA", "DRSStorage", "test_vm", 20)

        #assert
        self.assertEqual(result, 'mock exception')


    #def test_set_datastore_name(self):
    #    datacenter = create_autospec(vim.Datacenter("datacenter1"))
    #    datacenter.name = "old_name"
    #    self.content = self.session.content
    #    self.session.content.rootFolder.childEntity = Mock(return_value=[datacenter])
    #    object_renamer.rename_object(self,"old_name","new_name")

    def test_delete_vm_in_state_poweredoff_is_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime = Mock()
        vm.runtime.powerState = "poweredOff"
        vm.Destroy = Mock(return_value = vSphereMocks.get_success_task())
        self.session.get_obj = Mock(return_value = vm)

        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertTrue(vm.Destroy.called)
        self.assertEqual(result, "success")

    def test_delete_vm_in_state_poweredon_is_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.runtime = Mock()
        vm.runtime.powerState = "poweredOn"
        vm.Destroy = Mock(return_value = vSphereMocks.get_success_task())
        vm.PowerOff = Mock(return_value = vSphereMocks.get_success_task())
        self.session.get_obj = Mock(return_value = vm)

        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertTrue(vm.PowerOff.called)
        self.assertTrue(vm.Destroy.called)
        self.assertEqual(result, "success")

    def test_delete_vm_when_vm_not_found(self):
        #arrange
        self.session.get_obj = Mock(return_value = None)

        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertEqual(result, "cannot find vm test_vm")

    def test_delete_vm_with_exception(self):
        #arrange
        self.session.get_obj = Mock(side_effect=Exception("mock exception"))
        
        #act
        result = self.session.delete_vm("test_vm")

        #assert
        self.assertEqual(result, 'mock exception')

    def test_add_harddisk_to_vm_is_success(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        self.session.get_obj = Mock()
        def get_obj_mock(*args, **kwargs):
            if args[0][0] is vim.VirtualMachine:                
                vm.config = Mock()
                vm.config.hardware = Mock()
                virtualIDEController = create_autospec(vim.vm.device.VirtualIDEController)
                virtualIDEController.key = 1
                virtualIDEController.device = [Mock()]
                vm.config.hardware.device = [virtualIDEController]
                vm.Reconfigure = Mock(return_value = vSphereMocks.get_success_task())                
                return vm
            elif args[0][0] is vim.Datacenter:
                return create_autospec(vim.Datacenter)
            else:
                None
        self.session.get_obj.side_effect = get_obj_mock

        task = vSphereMocks.get_success_task()
        task.info.result = "some_path"
        self.session.si.content.virtualDiskManager.CreateVirtualDisk = Mock(return_value = task)

        #act
        result = self.session.add_harddisk_to_vm("192.168.42.72", "HA", "DRSStorage", "test_vm", 20)

        #assert
        self.assertTrue(self.session.si.content.virtualDiskManager.CreateVirtualDisk.called)
        self.assertTrue(vm.Reconfigure.called)
        self.assertEqual(result, 'success')

    def test_add_harddisk_to_vm_when_rollback(self):
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        self.session.get_obj = Mock()
        def get_obj_mock(*args, **kwargs):
            if args[0][0] is vim.VirtualMachine:
                vm.config = Mock()
                vm.config.hardware = Mock()
                virtualIDEController = create_autospec(vim.vm.device.VirtualIDEController)
                virtualIDEController.key = 1
                virtualIDEController.device = [Mock()]
                vm.config.hardware.device = [virtualIDEController]
                vm.Reconfigure = Mock(return_value = vSphereMocks.get_error_task("failed to add virtual disk"))
                return vm
            elif args[0][0] is vim.Datacenter:
                return create_autospec(vim.Datacenter)
            else:
                None
        self.session.get_obj.side_effect = get_obj_mock

        task = vSphereMocks.get_success_task()
        task.info.result = "some_path"
        self.session.si.content.virtualDiskManager.CreateVirtualDisk = Mock(return_value = task)

        #act
        result = self.session.add_harddisk_to_vm("192.168.42.72", "HA", "DRSStorage", "test_vm", 20)

        #assert
        self.assertTrue(self.session.si.content.virtualDiskManager.CreateVirtualDisk.called)
        self.assertTrue(vm.Reconfigure.called)
        self.assertTrue(self.session.si.content.virtualDiskManager.DeleteVirtualDisk.called)
        self.assertEqual(result, "failed to add virtual disk")

    def test_add_harddisk_to_vm_with_exception(self):
        #arrange
        self.session.get_obj = Mock(side_effect=Exception("mock exception"))
        
        #act
        result = self.session.add_harddisk_to_vm("192.168.42.72", "HA", "DRSStorage", "test_vm", 20)

        #assert
        self.assertEqual(result, 'mock exception')

    def test_set_vm_nic_is_success_when_windows7(self): 
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.guest = Mock()
        vm.guest.toolsStatus = "toolsInstalled"
        vm.guest.guestId = "windows7Server64Guest"
        self.session.get_obj_all_byname = Mock(return_value = [vm])
        vSphereMocks.set_start_program_in_guest(self)
        vSphereMocks.set_list_processes_success(self)

        #act
        result = self.session.set_vm_nic("test_vm", "administrator", "qs@L0cal", "192.168.30.250", "255.255.255.0", "192.168.30.1", "192.168.42.3", "192.168.42.2")

        #assert
        self.assertEqual(result, "IP Address configured successfully. Primary DNS configured successfully. Secondary DNS configured successfully.")

    def test_set_vm_nic_is_success_when_windows8(self): 
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.guest = Mock()
        vm.guest.toolsStatus = "toolsInstalled"
        vm.guest.guestId = "windows8Server64Guest"
        self.session.get_obj_all_byname = Mock(return_value = [vm])
        vSphereMocks.set_start_program_in_guest(self)
        vSphereMocks.set_list_processes_success(self)

        #act
        result = self.session.set_vm_nic("test_vm", "administrator", "qs@L0cal", "192.168.30.250", "255.255.255.0", "192.168.30.1", "192.168.42.3", "192.168.42.2")

        #assert
        self.assertEqual(result, "IP Address configured successfully. Primary DNS configured successfully. Secondary DNS configured successfully.")

    def test_set_vm_nic_call_fail_when_os_unknown(self): 
        #arrange
        vm = create_autospec(vim.VirtualMachine)
        vm.guest = Mock()
        vm.guest.toolsStatus = "toolsInstalled"
        vm.guest.guestId = "windowsXP"
        vm.config = Mock()
        vm.config.instanceUuid = "53ad0d00-ae40-4aa7-8648-5bca5726a57f"
        self.session.get_obj_all_byname = Mock(return_value = [vm])
        vSphereMocks.set_start_program_in_guest(self)
        vSphereMocks.set_list_processes_success(self)

        #act
        result = self.session.set_vm_nic("test_vm", "administrator", "qs@L0cal", "192.168.30.250", "255.255.255.0", "192.168.30.1", "192.168.42.3", "192.168.42.2")

        #assert
        self.assertEqual(result, "Guest OS 'windowsXP' found on VM 'test_vm' (53ad0d00-ae40-4aa7-8648-5bca5726a57f) is not currently supported.")

    def test_set_vm_nic_with_exception(self):
        #arrange
        self.session.get_obj_all_byname = Mock(side_effect=Exception("mock exception"))
        #act
        result = self.session.set_vm_nic("test_vm", "administrator", "qs@L0cal", "192.168.30.250", "255.255.255.0", "192.168.30.1", "192.168.42.3", "192.168.42.2")
        #assert
        self.assertEqual(result, 'mock exception')


if __name__ == '__main__':
   if is_running_under_teamcity():
        runner = TeamcityTestRunner() 
   else:
        runner = unittest.TextTestRunner()
   unittest.main(testRunner=runner)
