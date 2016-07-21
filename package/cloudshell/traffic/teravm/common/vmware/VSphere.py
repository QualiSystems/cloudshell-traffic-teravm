from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect

import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE

import requests

import json
import time
import object_renamer
import re
import threading

from vCenterExceptions import VmWareObjectNotFoundException

requests.packages.urllib3.disable_warnings()
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE


class VSphere:
    def __init__(self, disconnect=Disconnect, vim=vim, address='', user='', password=''):
        try:
            # self.logger = qs_logger.getQSLogger(handler_name="vSphereDriver")
            # self.si = connect(host=address, user=user, pwd=password, port=443)
            self.si = SmartConnect(
                host=address,
                user=user,
                pwd=password,
                port=443,
                sslContext=context
            )
            self.content = self.si.RetrieveContent()
            self.vim = vim
            self.disconnect = disconnect
        except Exception as e:
            print('======================' + str(e))

    def __del__(self):
        self.disconnect(self.si)


    ###############################################
    #                    HOSTS #
    ###############################################

    def powerOff(self, name):
        try:
            vm = self.get_obj([self.vim.VirtualMachine],name)

            if vm.runtime.powerState == 'poweredOff':
                return "%s already poweredOff" % name
            else:
                task_info = self.wait_task(vm.PowerOff())
                if(task_info.state == "error"):
                    return "error powering off %s error:%s" % (name,task_info.error.msg)

                return "%s poweredOff" % name
        except Exception as e:
            self.logger.error(e)
            return e.msg

    def powerOn(self, name):
        try:
            vm = self.get_obj([self.vim.VirtualMachine],name)

            if vm.runtime.powerState == 'poweredOn':
                return "%s already poweredOn" % name
            else:
                task_info = self.wait_task(vm.PowerOn())
                if(task_info.state == "error"):
                    return "error powering on %s error:%s" % (name,task_info.error.msg)

                return "%s poweredOn" % name
        except Exception as e:
            self.logger.error(e)
            return e.msg

    def suspend(self, name):
        try:
            vm = self.get_obj([self.vim.VirtualMachine],name)
            if vm.runtime.powerState == 'suspended':
                return "%s already suspended" % vm.name
            elif vm.runtime.powerState == "poweredOff":
                return "%s powered off" % vm.name
            else:
                task_info = self.wait_task(vm.Suspend())
                if(task_info.state == "error"):
                    return "error suspending %s error:%s" % (name, task_info.error.msg)
                return "%s suspended" % vm.name
        except Exception as e:
            self.logger.error(e)
            return e.msg

    def get_obj(self, vimtype, name):
        obj = self.try_get_obj(vimtype,name)
        if obj is None:
            raise VmWareObjectNotFoundException(name)
        return obj

    def try_get_obj(self, vimtype, name):
        obj = None
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break        
        return obj

    def get_obj_all(self, vimtype):        
        return self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)

    def get_obj_all_byname(self, vimtype, name):
        objects = []
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                objects.append(c)                
        return objects

    """
    Method to create a new cluster    
    :param cluster_name: Name of cluster to be created.
    :param datacenter_name: The location where the cluster will be craeted. E.g - name of datacenter that will contain the cluster.
    :param cluster_spec: sets the cluster definitions
    :param ha_enabled: Possible values : True / False
    :drs_enabled: Possible values : True / False
    :drs_automation_level: Possible values : fullyAutomated, manual, and partiallyAutomated
    """
    def create_cluster(self,cluster_name,cluster_location, ha_enabled, drs_enabled, drs_automation_level):
        message = None
        try:
           datacenter = self.get_obj([self.vim.Datacenter],cluster_location)
           host_folder = datacenter.hostFolder
              
           cluster_spec = self.vim.cluster.ConfigSpecEx()
           drs_config = self.vim.cluster.DrsConfigInfo()
           drs_config.enabled = drs_enabled
           drs_config.defaultVmBehavior = drs_automation_level
           drs_config.vmotionRate = 3
           cluster_spec.drsConfig = drs_config

           das_config = self.vim.cluster.DasConfigInfo()
           das_config.enabled = ha_enabled
           das_config.hostMonitoring = "enabled"
           das_config.failoverLevel = 1
           das_config.admissionControlEnabled = True

           default_vm_settings = self.vim.cluster.DasVmSettings()
           default_vm_settings.restartPriority = "medium"
           default_vm_settings.isolationResponse = "shutdown"

           vm_tools_monitoring = self.vim.cluster.VmToolsMonitoringSettings()
           vm_tools_monitoring.enabled = True
           vm_tools_monitoring.failureInterval = 30
           vm_tools_monitoring.minUpTime = 120
           vm_tools_monitoring.maxFailures = 3
           vm_tools_monitoring.maxFailureWindow = 3600
       
           default_vm_settings.vmToolsMonitoringSettings = vm_tools_monitoring
           das_config.defaultVmSettings = default_vm_settings
           cluster_spec.dasConfig = das_config

           dpm_config = self.vim.cluster.DpmConfigInfo()
           dpm_config.enabled = False
           dpm_config.hostPowerActionRate = 3
           cluster_spec.dpmConfig = dpm_config

           message = None
           cluster = host_folder.CreateClusterEx(name= cluster_name, spec=cluster_spec)

           message = "cluster: %s created under: %s" % (cluster_name ,cluster_location)
           self.logger.info(message)
        except Exception as e:
           self.logger.exception(e)
           message = e.msg

        return message
    
    """
    Method to delete a cluster
    :param cluster_name: the name of the cluster to delete
    """
    def delete_cluster(self,cluster_name):
        try:
            cluster = self.get_obj([self.vim.ClusterComputeResource],cluster_name)
            cluster.Destroy()  
            return "cluster %s deleted" % cluster_name            
        except Exception as e:
            self.logger.error(e)
            return e.msg
          
    """
    Method to create a datacenter container under the root folder
    :param datacenter_name: the name of the new datacenter to create
    """
    def create_datacenter(self, datacenter_name):
        try:
            if len(datacenter_name) > 79:
                raise ValueError("The name of the datacenter must be under 80 characters.")

            self.logger.info("Creating datacenter '{0}'".format(datacenter_name))

            # get root forlder object
            rootfolder = self.si.content.rootFolder

            # create datecenter
            rootfolder.CreateDatacenter(name=datacenter_name)

            message = "Created datacenter '{0}' succesfully".format(datacenter_name)
            self.logger.info(message)
            return message

        except Exception as e:
           self.logger.exception(e)
           return e.msg
    
    """
    Method to delete a datacenter 
    :param datacenter_name: the datacenter to delete
    """
    def delete_datacenter(self, datacenter_name):
        try:
            datacenter = self.get_obj([self.vim.Datacenter], datacenter_name)
            datacenter.Destroy()
            return "datacenter %s deleted" % datacenter_name
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to enable/disable lockdown mode on a specific vm host. 
    If lockdown mode is already disabled or already enabled accordingly than method will do nothing.
    :param host_name: host on which to enable/disable lockdown mode 
    :param enable_lockdown: True - enable lockdown mode ; False - exit lockdown mode
    """
    def set_lockdown_mode(self, host_name, enable_lockdown=True):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)           
            adminDisabled = host.config.adminDisabled

            if enable_lockdown:
                if adminDisabled:
                    message = "Lockdown mode is already enabled, nothing to do"
                else:
                    host.EnterLockdownMode()
                    # check that we entered lockdown mode successfully                    
                    message = "Finished enabling lockdown mode succesfully" if host.config.adminDisabled else "Failed enabling lockdown mode"
            else:
                if adminDisabled:
                    host.ExitLockdownMode()
                    # check that we entered lockdown mode successfully                    
                    message = "Finished exiting lockdown mode succesfully" if not host.config.adminDisabled else "Failed exiting lockdown mode"
                else:
                    message = "Lockdown mode is already disabled, nothing to do"
                    
            message = "{0}. Host: {1}".format(message, host_name)
            self.logger.info(message)
            return message
         
        except Exception as e:
           self.logger.exception(e)
           return e.msg

    """
    Method to set the start order and start delay for VM
    :param vm_name: The name of the VM to set the starup priority. 
                    If more than one VM found with the same name, all will be updated.
    :param start_order: The startup order of the VM, where 1 is the hightest priority. 
                        To remove the priority from a VM set start_order to -1.
    :param start_delay: Delay in seconds before continuing with the next virtual machine in the order of machines to be started.
                        If the delay is specified as -1, then the system default is used.
    """
    def set_vm_startup_priority(self, vm_name, start_order, start_delay):
        try:
            self.logger.info("Starting to set startup priority of {0} with start delay of {1} for vm name {2}".format(start_order, start_delay, vm_name))

            # get vms with vm_name
            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vm_name)

            for vm in vms:                
                # init auto start config
                auto_power_cfg = self.vim.host.AutoStartManager.AutoPowerInfo()
                auto_power_cfg.key = vm
                auto_power_cfg.startOrder = start_order
                auto_power_cfg.startDelay = start_delay
                auto_power_cfg.startAction = "none" if start_order is -1 else "powerOn"  # need to set start action to 'powerOn' if startOrder is positive else if
                                                                                         # startOrder is -1 set to 'None'
                if start_order is -1:
                    auto_power_cfg.stopAction = "none"
                auto_power_cfg.waitForHeartbeat = "systemDefault"
                # set auto start config in auto start manager
                cfg = self.vim.host.AutoStartManager.Config()
                cfg.powerInfo.append(auto_power_cfg)
                # update new configuration on host object
                vm.summary.runtime.host.configManager.autoStartManager.Reconfigure(spec=cfg)

            return "Successefully updated startup priority"

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to enable/disalble start policy for specific host
    :param vmname: name of host
    :param enable_start_policy: True - Enable start policy ; False - Disable start policy
    """        
    def set_vmhost_start_policy(self, host_name, enable_start_policy=True):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
            if enable_start_policy:
                msg_action = "enabled"
            else:
                msg_action = "disabled"
            #check if start policy should be enabled/disalbed
            if host.configManager.autoStartManager.config.defaults.enabled != enable_start_policy:
                cfg = self.vim.host.AutoStartManager.Config()
                cfg.defaults = self.vim.host.AutoStartManager.SystemDefaults()
                cfg.defaults.enabled = enable_start_policy
                host.configManager.autoStartManager.Reconfigure(spec=cfg)
                message = "Successfully {0} start policy on vmhost {1}".format(msg_action, host_name)
            else:
                message = "Start policy on vmhost {0} is already {1}".format(host_name, msg_action)
            self.logger.info(message)
        except Exception as e:
            self.logger.exception(e)
            message = e.msg

        return message    

    """
    Method to restart a host
    :param host_name: the host to reboot
    """
    def restart_host(self, host_name,force):
        try:
            host = self.get_obj([self.vim.HostSystem],host_name)
            if host.runtime.powerState == 'poweredOff' or host.runtime.powerState == 'poweredOn':
                host.Reboot(force)
                message = "host: %s rebooted" % host.name
                self.logger.info(message)
            else:
                message = "host: %s power state is unknown, taking no action" % host.name
        except Exception as e:
            self.logger.exception(e)
            message = e.msg
            
        return message    

    """
    Method to get the vm's hard disks

    :param vm_name: the vm which to retrieve the disks from
    :returns: disk_info json
    """
    def get_hard_disks(self, vm_name):
        try:
            vm = self.get_obj([self.vim.VirtualMachine],vm_name)
            hardware = vm.config.hardware

            disks = [device for 
                    device in hardware.device 
                    if isinstance(device, self.vim.vm.device.VirtualDisk)]

            disks_info = [{
                "diskObjectId" : disk.diskObjectId,
                "fileName" :disk.backing.fileName,
                "label":disk.deviceInfo.label,
                "capacityInBytes": disk.capacityInBytes
                } for disk in disks]
            
            self.logger.info("getting disks for %s" % vm_name)
            return json.dumps(disks_info)
        except Exception as e:
            self.logger.exception(e)
            return e.msg     

        """
        Method to get all the data storages
        """

    """
    Method to get all the avilable data stores
    """
    def get_available_datastores(self):
        try:
             hosts = self.content.viewManager.CreateContainerView(self.content.rootFolder,[self.vim.HostSystem],True)
             esxi_hosts = hosts.view
             datastores = {}
         
             for esxi_host in esxi_hosts:
           
                # All Filesystems on ESXi host
                storage_system = esxi_host.configManager.storageSystem
                host_file_sys_vol_mount_info = None

                try:
                    host_file_sys_vol_mount_info = storage_system.fileSystemVolumeInfo.mountInfo
                except IndexError:
                    continue

                datastore_dict = {}
                # Map all filesystems
                for host_mount_info in host_file_sys_vol_mount_info:
                    # Extract only VMFS volumes
                    if host_mount_info.volume.type == "VMFS":

                        extents = host_mount_info.volume.extent
                    
                        datastore_details = {
                            'uuid': host_mount_info.volume.uuid,
                            'capacity': host_mount_info.volume.capacity,
                            'vmfs_version': host_mount_info.volume.version,
                            'local': host_mount_info.volume.local,
                            'ssd': host_mount_info.volume.ssd
                        }

                        extent_arr = []
                        extent_count = 0
                        for extent in extents:
                            # create an array of the devices backing the given
                            # datastore
                            extent_arr.append(extent.diskName)
                            # add the extent array to the datastore info
                            datastore_details['extents'] = extent_arr
                            # associate datastore details with datastore name
                            datastore_dict[host_mount_info.volume.name] = datastore_details

                # associate ESXi host with the datastore it sees
                datastores[esxi_host.name] = datastore_dict
             result = json.dumps(datastores)

             return result      
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to rename a datastore
    :param datastore_name:the datastore name to change
    :param new_name:the new name
    """
    def set_datastore_name(self, datastore_name,new_name):
        try:
            return object_renamer.rename_object(self,datastore_name, new_name)
        except Exception as e:
            self.logger.error(e)
            return e.msg
      
    """
    Method to extend Hard Disk capacity
    :param datacenter_name: the name of the datacenter
    :param file_path: the path to the vmdk file
    :capacityGB : the new capacity to set in the virtual hard disk
    note - decreasing the size of the vdh is not supported
    """
    def extend_hard_disk_capacity(self, datacenter_name, file_path, capacityGB):
        try:
            capacityKB = capacityGB * 1024 * 1024
            datacenter = self.get_obj([self.vim.Datacenter],datacenter_name)
            task = self.si.content.virtualDiskManager.ExtendVirtualDisk(file_path,datacenter,capacityKB,False)
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)

            if task.info.state == "error":
                message = "error reconfiguring %s. %s" % (file_path,task.info.error.msg)
                self.logger.error(message)
                return message

            message = "Reconfiguring %s complete" % file_path
            self.logger.info(message)
            return message
        except Exception as e:
            self.logger.error(e)
            return e.msg      

    """
    method to get the esxi version
    :param vi_host: vi server to query
    """
    def get_esxi_version(self, vi_host):
        try:
             host = self.content.searchIndex.FindByDnsName(dnsName = vi_host, vmSearch = False)
             if host == None:
                self.logger.error("could not find host %s", host_name)
             return host.config.product.version
        except Exception as e:
             self.logger.error(e)
             return e

    """
    Method to set the host in maintenance mode
    :param vm_host: vi server to set
    :enable_maintnance_mode: true to enable maintenance mode, false to disable maintnance mode
    """
    def set_maintenance_mode(self, vi_host, enable_maintnance_mode):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = vi_host, vmSearch = False)
            if host == None:
                self.logger.error("could not find host %s" % vi_host)
                return "could not find host %s" % vi_host
            
            task = None
            if enable_maintnance_mode == True:
                task = host.EnterMaintenanceMode(0)
            else:
                task = host.ExitMaintenanceMode(0)

            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:                
                 time.sleep(1)
            
            if task.info.state == "error":
                message = "error reconfiguring maintenance mode %s %s" % (vi_host, task.info.error.msg)
                self.logger.error(message)
                return message

            action = "enabled" if enable_maintnance_mode else "diabled"
            message = "maintnance mode on %s is now %s" % (vi_host, action)
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to set the scratch file location
    :param host_name: the host machine which determines the file name
    :param data_store: the datastore where to set the new folder
    :param data_center: the datacenter where to run the operation

    note - could not find a way to check if the folder already exists so 
           for now I"m hiding the exception
    """
    def set_persistent_scratch_location(self, host_name, data_store_to_use,datacenter_name):
        try:
            datacenter = self.get_obj([self.vim.Datacenter], datacenter_name)
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)  
            if host == None:
                message ="could not find host %s" % host_name
                self.logger.error(message)     
                return message
            datastore = [ds for ds in host.datastore if ds.name == data_store_to_use]
       
            if len(datastore) == 0:
                message = "datastore %s does not exist"
                self.logger.error(message)
                return message
        
            host_name_fixed = re.sub(r"[<>/:;{}[\]~`.]","",host_name)
            datastore = datastore[0]
            folder = "locker_" + host_name_fixed
            dir_name = "[" + datastore.name + "] " + folder
            
            try:
                self.content.fileManager.MakeDirectory(dir_name,datacenter, False)
            except self.vim.fault.FileAlreadyExists as e:
                self.logger.info("file already exists")

            opt = self.vim.option.OptionValue()
            opt.key = "ScratchConfig.ConfiguredScratchLocation"
            opt.value = "/vmfs/volumes/" + datastore.name + "/" + folder
            host.configManager.advancedOption.UpdateValues([opt])

            message = "scratch location set to %s" % dir_name
            self.logger.info(message)
            return message
        except Exception as e:
            self.logger.error(e)
       
    """
    Method to get host details
    :param vm_host_name: host name
    :param location: host location (host container name)
    """
    def get_vmhosts(self, vm_host_name, location):
        try:
            self.logger.info("Starting to get VM host with name '{0}' in locaition '{1}'".format(vm_host_name, location))
            
            all_hosts = self.content.searchIndex.FindAllByDnsName(dnsName = vm_host_name, vmSearch = False)
            result = []

            for host in all_hosts:
                if host.name == vm_host_name:
                    if self._is_host_in_location(host, location):
                        runtime = host.summary.runtime
                        result.append({
                                "name" : host.name,
                                "connectionState" : runtime.connectionState,
                                "powerState" : runtime.powerState,
                                "numCpu" : host.hardware.cpuInfo.numCpuCores,
                                "cpuUsageMhz" : host.summary.hardware.cpuMhz
                            })

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to change the DNS server, domain name and virtual network host name for a specific VM host
    :param host_name: The VM host to update
    :param dns_servers: The new DNS servers. Must be a string array.
    :param new_domain: New domain name
    :param new_virtual_network_host_name: New host name for the virtual network of the host
    """
    def manage_host_dns_and_routing(self, host_name, dns_servers, new_domain, new_virtual_network_host_name):
        try:
            self.logger.info("Starting to manage dns and routing for host '{0}'. New DNS Servers: {1} ; New Domain: {2} ; New Netwrol Host Name: {3}".format(host_name, dns_servers, new_domain, new_virtual_network_host_name))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)

            # create empty config object
            dns_config = self.vim.host.DnsConfig()

            # init config object
            dns_config.domainName = new_domain
            dns_config.hostName = new_virtual_network_host_name
            dns_config.address = dns_servers

            # update dns config for current host
            host.configManager.networkSystem.UpdateDnsConfig(config = dns_config)

            return "Successfully updated dns and rounting configurations"

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to update/set an advanced parameter on a specific host
    :param host_name: The VM host to update
    :param param_name: The name of the parameter to update
    :param param_value: The new value of the parameter
    *Note: ChoiceOption parameter type is currently not supported by this method
    """
    def set_host_advanced_parameter(self, host_name, param_name, param_value):
        try:
            self.logger.info("Starting to update advanced parameter '{0}' with value '{1}' for host '{2}'".format(param_name, param_value, host_name))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)

            for opt in host.configManager.advancedOption.supportedOption:
                if opt.key == param_name:
                    # check data type and fix param_value accordingly
                    if type(opt.optionType) is self.vim.option.BoolOption: 
                        param_value = bool(param_value)
                    elif type(opt.optionType) is self.vim.option.ChoiceOption: 
                        raise ValueError("parameter type is 'ChoiceOption' - its not supported")
                    elif type(opt.optionType) is self.vim.option.FloatOption: 
                        param_value = float(param_value)
                    elif type(opt.optionType) is self.vim.option.IntOption: 
                        param_value = int(param_value)
                    elif type(opt.optionType) is self.vim.option.LongOption: 
                        param_value = long(param_value)
                    elif type(opt.optionType) is self.vim.option.StringOption: 
                        param_value = str(param_value)
                    break

            # create a key value pair object
            kvp = self.vim.option.OptionValue()
            # wrap kvp in array
            kvp_arr = [kvp]

            # init key value pair object
            kvp.key = param_name
            kvp.value = param_value

            # update param
            host.configManager.advancedOption.UpdateValues(changedValue = kvp_arr)

            return "Successfully updated advanced parameter"

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to enable/disable firwall rules on a specific host
    :param host_name: The VM host to update
    :param firewall_exception: The name of the firewall rule
    :param enable_exception: True - enable rule ; False - disable rule
    """
    def set_host_firwall(self, host_name, firewall_exception, enable_exception):
        try:
            self.logger.info("Starting to update firewall exception '{0}' with state '{1}' for host '{2}'".format(firewall_exception, enable_exception, host_name))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)

            # find firewall exception key
            firewall_exception_key = None
            for f in host.configManager.firewallSystem.firewallInfo.ruleset:
                if f.label == firewall_exception:
                    if f.enabled == enable_exception:
                        print "Firewall exception '{0}' is already {1}, nothing to do.".format(firewall_exception, "enabled" if enable_exception else "disabled")
                        return
                    firewall_exception_key = f.key
                    break

            if firewall_exception_key is None:
                raise ValueError("Firewall exception name '{0}' doesnt exist".format(firewall_exception))

            if enable_exception:
                host.configManager.firewallSystem.EnableRuleset(id = firewall_exception_key)
            else:
                host.configManager.firewallSystem.DisableRuleset(id = firewall_exception_key)
            
            return "Successfully updated firewall exception state"

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to add NTP servers to a host. If NTP server already exist it will not cause a fault. 
    Method also enables firewall rule for the NTP service and starts the NTP service if needed.
    :param host_name: The VM host to update the NTP server on
    :param ntp_servers: List of new NTP server to add
    """
    def set_host_ntp(self, host_name, ntp_servers):
        try:
            self.logger.info("Starting to add ntp servers '{0}' to host '{1}".format(ntp_servers, host_name))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)

            # NTP manager on ESXi host
            date_time_manager = host.configManager.dateTimeSystem

            # configure NTP Servers
            ntpServers = ntp_servers if isinstance(ntp_servers, (list, tuple)) else [ntp_servers]
            currentNtpServers = date_time_manager.dateTimeInfo.ntpConfig.server
            # check new ntp_servers not exist in currentNtpServers
            if not isinstance(currentNtpServers, list):
                currentNtpServers = []
            for new_ntp in ntpServers:
                if new_ntp not in currentNtpServers:
                    currentNtpServers.append(new_ntp)
            ntpConfig = self.vim.HostNtpConfig(server=currentNtpServers)
            dateConfig = self.vim.HostDateTimeConfig(ntpConfig=ntpConfig)
            date_time_manager.UpdateDateTimeConfig(config=dateConfig)

            # configure firewall to enable ntpd service exception rule
            print self.set_host_firwall(host_name, "NTP Client", True)

            # find ntpd service instance
            ntpd_service = None
            for service in host.configManager.serviceSystem.serviceInfo.service:
                if service.key == "ntpd":
                    ntpd_service = service
                    break

            # serivce manager
            serviceManager = host.configManager.serviceSystem

            # update service policy to "automatic" if needed
            if ntpd_service.policy != "automatic":
                serviceManager.UpdatePolicy(id='ntpd',policy="automatic")

            # check ntpd service status
            if ntpd_service.running:
                # restart ntpd service
                print "Restarting ntpd service on " + host_name
                serviceManager.Restart(id='ntpd')
            else:
                # start ntpd service
                print "Starting ntpd service on " + host_name
                serviceManager.Start(id='ntpd')

            return "Successfully updated ntp servers"

        except Exception as e:
            self.logger.exception(e)
            return e


    ###############################################
    #                  NETWORKING #
    ###############################################
    
    """
    Method to remove a port group
    :param host_name: the host where to add the port group to
    :param port_group_name: the port group name
    """
    def remove_port_group(self, host_name, port_group_name):
        success = True
        try:      
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                  
            host.configManager.networkSystem.RemovePortGroup(port_group_name) 
            self.logger.info("Removed port group %s from host %s" % (port_group_name, host_name))
        except Exception as e:
            self.logger.error(e)
            success = False

        return success

    """
    Method to add a vlan
    :param host_name: the host for the vlan
    :param v_switch_name: the vswitch for the vlan
    :param port_group_name: the port group in the vswitch
    """
    def add_vlan(self, host_name, v_switch_name, port_group_name, vlan_id):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
        
            port_group = [pg for pg in host.config.network.portgroup if pg.spec.name == port_group_name]

            if len(port_group) == 0:
                port_group_ok = self.new_virtual_port_group(host_name, v_switch_name, port_group_name, vlan_id)
                if port_group_ok == True:
                    port_group = [pg for pg in host.config.network.portgroup if pg.spec.name == port_group_name]
                else:
                    return
        
            spec = self.vim.host.PortGroup.Specification()
            spec.name = port_group_name
            spec.vlanId = vlan_id
            spec.vswitchName = v_switch_name
            spec.policy = self.vim.host.NetworkPolicy()

            host.configManager.networkSystem.UpdatePortGroup(port_group_name, spec)
            message = "vlan (id=%s) added to port group %s" % (vlan_id, port_group_name)
            self.logger.info(message)
            return message
        except Exception as e:
            self.logger.error(e)
            return e.msg
    
    """
    Method to add vm kernel networking
    :param host_name: the host to configure
    :param port_group: the port group to configure
    :param ip_address:
    :param subnet_mask:
    """
    def add_vmkernel_networking(self, host_name, port_group_name, ip_address,subnet_mask, vlan_id,vmotion_active, v_switch_name):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
        
            network_system = host.configManager.networkSystem
            vmotion_system = host.configManager.vmotionSystem

            spec = self.vim.host.PortGroup.Specification()
            spec.name = port_group_name
            spec.vlanId = vlan_id
            spec.vswitchName = v_switch_name
            spec.policy = self.vim.host.NetworkPolicy()

            self.logger.info("updating vlan id %s in portgroup %s" % (vlan_id, port_group_name))
            host.configManager.networkSystem.UpdatePortGroup(port_group_name, spec)

            nicspec = self.vim.host.VirtualNic.Specification()
            nicspec.ip = self.vim.host.IpConfig()
            nicspec.ip.dhcp = True if ip_address == None else False
            nicspec.ip.ipAddress = ip_address
            nicspec.ip.subnetMask = subnet_mask

            self.logger.info("adding virtual nic to %s" % port_group_name)
            device = network_system.AddVirtualNic(port_group_name,nicspec)
        
            if(vmotion_active == True):
                self.logger.info("selecting vnic %s for vmotion" % device)
                vmotion_system.SelectVnic(device)            

            message = "done adding vm kernel networking"
            self.logger.info(message)
            return message
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to get all VMKernel network adapters 
    """
    def get_vmk(self):
        try:
            self.logger.info("Starting to get VMK")
            
            vmkDic = {}
            result = []
            vmkPortGroupName = 'VMkernel'

            hosts = self.get_obj_all([self.vim.HostSystem])

            # get all VMKernel network adapters
            for c in hosts.view:
                cfg = c.config
                for netCfg in cfg.virtualNicManagerInfo.netConfig:
                    for vnic in netCfg.candidateVnic:
                        if vnic.portgroup == vmkPortGroupName:
                            if vnic.device not in vmkDic:
                                vmkDic[vnic.device] = 1
                                result.append({
                                    "name" : vnic.device,
                                    "portGroupName" : vmkPortGroupName
                                    })

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to get details of specific vswitch on specific vmhost
    :param name: vswitch name to get
    :param vmhost: host where to look for the vswitch
    """
    def get_v_switch(self, name, vmhost):
        try:
            self.logger.info("Starting to get virtual switch details for switch name '{0}' on host '{1}'".format(name, vmhost))
            
            host = self.content.searchIndex.FindByDnsName(dnsName = vmhost, vmSearch = False)
            result = []
            for vs in host.config.network.vswitch:
                if vs.name == name:
                    result.append({
                        "name" : vs.name,
                        "numOfPorts" : vs.numPorts,
                        "numPortsAvailable" : vs.numPortsAvailable,
                        "mtu" : vs.mtu,
                        "key" : vs.key
                    })

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e
    
    """
    Method to get network adapters on specific vmhost
    :param vmhost: host for witch to get network adapters
    :param getOnlyPhysical: False -> get all network adapters (virtual & physical) ; True -> get only physical network adapters
    """
    def get_vmhost_network_adapters(self, vmhost, getOnlyPhysical):
        try:
            self.logger.info("Starting get_vmhost_network_adapters. Host '{0}', getOnlyPhysical: {1}".format(vmhost, getOnlyPhysical))
            
            host = self.content.searchIndex.FindByDnsName(dnsName = vmhost, vmSearch = False)        
            result = []

            if not getOnlyPhysical:
                for vnic in host.config.network.vnic:
                    spec = vnic.spec
                    ip = spec.ip
                    result.append({
                            "name" : vnic.device,
                            "mac" : spec.mac,
                            "dhcpEnabled" : ip.dhcp,
                            "ip" : ip.ipAddress,
                            "subnetMask" : ip.subnetMask
                        })

            for pnic in host.config.network.pnic:
                ip = pnic.spec.ip
                result.append({
                        "name" : pnic.device,
                        "mac" : pnic.mac,
                        "dhcpEnabled" : ip.dhcp,
                        "ip" : ip.ipAddress,
                        "subnetMask" : ip.subnetMask
                    })

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to configure distributed virtual switch with a physical network adapter
    :param host_name: host that contains the physical network adapter
    :param host_pysical_nic_name: physical network adapter name
    :param dvs_name: distributed virtual switch name
    """
    def add_host_physical_adapter_to_dvswitch(self, host_name, host_pysical_nic_name, dvs_name):
        try:
            dvs = self.get_obj([self.vim.DistributedVirtualSwitch], dvs_name)
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)        
            
            # find the physical nic object
            pnic_obj = None
            for pnic in host.configManager.networkSystem.networkConfig.pnic:
                if pnic.device == host_pysical_nic_name:
                    pnic_obj = pnic
                    break
            if pnic_obj is None:
                raise ValueError("Physical network adapter '{0}' is not found on host '{1}'").format(host_pysical_nic_name, host_name)            
            
            # check if host exist in dvs
            exist_host = False
            exist_pnic = False
            for dvs_host in dvs.config.host:
                if host.config.host.name == dvs_host.config.host.name:
                    exist_host = True
                    for dvs_host_pnic in dvs_host.config.backing.pnicSpec:
                        if pnic_obj.device == dvs_host_pnic.pnicDevicedevice:
                            exist_pnic = True
                            break
                    break

            if exist_host and exist_pnic:
                message = "Physical network adapter '{0}' is already in dvswitch '{1}'".format(host_pysical_nic_name, dvs_name)
                self.logger.info(message)
                return message

            hostSpec = self.vim.dvs.HostMember.ConfigSpec()
            hostSpec.host = host

            if exist_host:
                hostSpec.operation = self.vim.ConfigSpecOperation().edit
            else:
                hostSpec.operation = self.vim.ConfigSpecOperation().add
           

            hostSpec.backing = self.vim.dvs.HostMember.PnicBacking()
            pnicSpec = self.vim.dvs.HostMember.PnicSpec()
            pnicSpec.pnicDevice = host_pysical_nic_name
            hostSpec.backing.pnicSpec = [pnicSpec]
            
            spec = self.vim.DistributedVirtualSwitch.ConfigSpec()
            spec.configVersion = dvs.config.configVersion
            spec.host = [hostSpec]
                
            task = dvs.ReconfigureDvs_Task(spec)

            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":
                message = "Error configuring dvSwitch '{0}' with pysical network adapter '{1}' from host '{2}'. {3}".format(dvs_name, host_pysical_nic_name, host_name, task.info.error.msg)
                self.logger.error(message)    
                return message

            message = "Successfully configured dvSwitch '{0}' with pysical network adapter '{1}' from host '{2}'".format(dvs_name, host_pysical_nic_name, host_name)
            self.logger.info(message)    
            return message

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to add a host to a distributed virtual swtich
    :param host_name: host name
    :param dvs_name: distributed virtual switch name
    """
    def add_host_to_virtual_switch(self, dvs_name, host_name_toadd):
        try:
            dvs = self.get_obj([self.vim.DistributedVirtualSwitch], dvs_name)
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name_toadd, vmSearch = False)        

            # check if host exist in dvs
            for dvs_host in dvs.config.host:
                if host.config.host.name == dvs_host.config.host.name:
                    message = "Physical network adapter '{0}' is already in dvswitch '{1}'".format(host_name_toadd, dvs_name)
                    self.logger.info(message)
                    return message

            hostSpec = self.vim.dvs.HostMember.ConfigSpec()
            hostSpec.host = host
            hostSpec.operation = self.vim.ConfigSpecOperation().add
            
            spec = self.vim.DistributedVirtualSwitch.ConfigSpec()
            spec.configVersion = dvs.config.configVersion
            spec.host = [hostSpec]
                
            task = dvs.ReconfigureDvs_Task(spec)

            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":
                message = "Error add host '{1}' to dvSwitch '{0}'. {2}".format(dvs_name, host_name_toadd, task.info.error.msg)
                self.logger.error(message)    
                return message

            message = "Successfully added host '{1}' to dvSwitch '{0}'".format(dvs_name, host_name_toadd)
            self.logger.info(message)    
            return message

        except Exception as e:
            self.logger.exception(e)
            return e

    def remove_host_from_virtual_switch(self,dvs_name,host_name_to_remove):
        try:
            dvs = self.get_obj([self.vim.DistributedVirtualSwitch], dvs_name)
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name_to_remove, vmSearch = False)   
            
            hostSpec = self.vim.dvs.HostMember.ConfigSpec()
            hostSpec.host = host
            hostSpec.operation = self.vim.ConfigSpecOperation().remove
            
            spec = self.vim.DistributedVirtualSwitch.ConfigSpec()
            spec.configVersion = dvs.config.configVersion
            spec.host = [hostSpec]
                
            task = dvs.ReconfigureDvs_Task(spec)

            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":
                message = "Error removing host '{1}' from dvSwitch '{0}'. {2}".format(dvs_name, host_name_to_remove, task.info.error.msg)
                self.logger.error(message)    
                return message
     
            message = "Successfully removed host '{1}' from dvSwitch '{0}'".format(dvs_name, host_name_to_remove)
            self.logger.info(message)    
            return message

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to connect between a distributed virtual port group and a virtual NIC
    :param host_name: host name where the virtual NIC is located
    :param vmk_name: name of the virtual NIC
    :param dvs_name: distributed virtual switch name where the distributed virtual port group is located
    :param virtual_port_group: the distributed virtual port group name
    """
    def add_vmkernel_to_dvswitch(self, host_name, vmk_name, dvs_name, virtual_port_group):
        try:
            self.logger.info("Starting to connect between a distributed virtual port group '{0}' (under a distributed virtual switch '{1}') and a virtual NIC '{2}' on host '{3}'" \
                             .format(virtual_port_group, dvs_name, vmk_name, host_name))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)        
            dvs = self.get_obj([self.vim.DistributedVirtualSwitch], dvs_name)
            
            # check that vnic exist
            vnic_exist = False
            for vnic in host.configManager.networkSystem.networkConfig.vnic:
                if vnic.device == vmk_name:
                    vnic_exist = True
                    break
            
            if not vnic_exist:
                message = "Virtual NIC '{0}' not found".format(vmk_name)
                self.logger.error(message)
                return message
            
            # check port group exist
            vpg = None
            for port_group in dvs.portgroup:
                if port_group.name == virtual_port_group:
                    vpg = port_group
                    break

            if vpg is None:
                message = "Distributed virtual port group '{0}' not found".format(virtual_port_group)
                self.logger.error(message)
                return message

            spec = self.vim.host.VirtualNic.Specification()
            spec.distributedVirtualPort = self.vim.dvs.PortConnection()
            spec.distributedVirtualPort.switchUuid = dvs.uuid
            spec.distributedVirtualPort.portgroupKey = vpg.key

            host.configManager.networkSystem.UpdateVirtualNic(device = vmk_name, nic = spec)

            message = "Successfully connected between a virtual NIC and distributed virtual port group"
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.exception(e)
            return e

    """
    Method to get the virtual port group data
    :param host_name:host to retrieve the port group data from
    return port groups JSON
    """
    def get_virtual_port_groups(self, host_name):
        try:
            self.logger.info("getting port groups data from %s" % host_name)
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return

            port_groups_data = {}
            port_groups = host.config.network.portgroup
            for pg in port_groups:
                port_group = {
                        "name" : pg.spec.name,
                        "vlanId" : pg.spec.vlanId,
                        "switchName" : pg.spec.vswitchName
                    }
                port_groups_data[port_group["name"]] = port_group
                       
            return json.dumps(port_groups_data)
        except Exception as e:
            self.logger.error(e)
            return e

    """
    Method to make a nic active
    :param host_name: the host to configure
    :param v_switch_name: the vswitch to configure
    :param vmnic: the vmnic to set as active
    """
    def make_nic_active(self, host_name, v_switch_name, vmnic_name):
        try:
            self.logger.info("setting vmnic %s on vswitch %s active" % (vmnic_name, v_switch_name))
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
            
            network_config = host.config.network
            network_system = host.configManager.networkSystem

            vswitch = [vswitch for vswitch in network_config.vswitch if vswitch.name == v_switch_name]
            if(len(vswitch) == 0):
                message = "cannot find vswitch %s" % vmnic_name
                self.logger.info(message)
                return message            
            
            vswitch = vswitch[0]
                
            vswitch_spec = vswitch.spec
            vswitch_spec.policy.nicTeaming.nicOrder = self.vim.host.NetworkPolicy.NicOrderPolicy()
            vswitch_spec.policy.nicTeaming.nicOrder.activeNic = vmnic_name

            network_system.UpdateVirtualSwitch(v_switch_name, vswitch_spec)

            message = "vmnic %s is now active on %s" % (vmnic_name, v_switch_name)
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to create a new virtual port group
    :param host_name: host name to configure
    :param v_switch_name: v_switch to configure
    :param port_group_name: the port group to configure
    :param vlan_id: the vlan Id to set
    """
    def new_virtual_port_group(self, host_name, v_switch_name, port_group_name, vlan_id=0):
        try:
            self.logger.info("creating new port group %s on vswitch %s" % (port_group_name, v_switch_name))
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
            
            network_config = host.config.network
            network_system = host.configManager.networkSystem

            spec = self.vim.host.PortGroup.Specification()
            spec.name = port_group_name
            spec.vlanId = vlan_id
            spec.vswitchName = v_switch_name
            spec.policy = self.vim.host.NetworkPolicy()
            network_system.AddPortGroup(spec)
            
            message = "Port group %s created on %s" % (port_group_name, v_switch_name)
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to set a vnic to a port group
    :param host_name: the host to configure
    :param kernel_adapter_ip: the ip address to set
    :param kernel_adapter_subnet_mask: the subnet mask to set
    :param portgroup_name: the port group to configure
    """
    def new_vmhost_net_adapter(self, host_name, kernel_adapter_ip, kernel_adapter_subnet_mask, portgroup_name):        
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
            
            network_config = host.config.network
            network_system = host.configManager.networkSystem

            nicspec = self.vim.host.VirtualNic.Specification()
            nicspec.ip = self.vim.host.IpConfig()
            nicspec.ip.dhcp = True if kernel_adapter_ip == None else False
            nicspec.ip.ipAddress = kernel_adapter_ip
            nicspec.ip.subnetMask = kernel_adapter_subnet_mask
            device = network_system.AddVirtualNic(portgroup_name,nicspec)
            
            message = "New adapter added to port group %s" % portgroup_name
            self.logger.info(message)
            return message
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to remove a vlan
    :param host_name: the host name to configure
    :param port_group_name: the port group to configure
    """
    def remove_vlan(self, host_name, port_group_name):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network
            network_system = host.configManager.networkSystem
            
            attached_vnic = [vnic for vnic in network_config.vnic if vnic.portgroup == port_group_name]
            if len(attached_vnic) > 0:
                attached_vnic = attached_vnic[0]
            else:
                attached_vnic = None

            if attached_vnic != None:
                network_system.RemoveVirtualNic(attached_vnic.device)

            network_system.RemovePortGroup(port_group_name)
            
            message = "Removed port group %s" % port_group_name
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to remove an assosiated vnic from a port group
    :param host_name: the host name to configure
    :param port_group_name: the port group to configure
    """
    def remove_vm_kernel(self, host_name, port_group_name):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network
            network_system = host.configManager.networkSystem
            
            attached_vnic = [vnic for vnic in network_config.vnic if vnic.portgroup == port_group_name]
            if len(attached_vnic) > 0:
                attached_vnic = attached_vnic[0]
            else:
                attached_vnic = None

            if attached_vnic != None:
                network_system.RemoveVirtualNic(attached_vnic.device)
                message = "Nic removed from %s" % port_group_name
                self.logger.info(message)
                return message
            else:
                message = "Could not find nic for %s" % port_group_name
                self.logger.error(message)
                return message
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to enable or disable failback
    :param host_name: the host to configure
    :param v_switch_name:the virtual switch to configure
    :param failback_enabled: true to enable false to disable
    """
    def enable_disable_failback(self, host_name,v_switch_name, failback_enabled):
         try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network
            network_system = host.configManager.networkSystem
           
            vswitch = [vswitch for vswitch in network_config.vswitch if vswitch.name == v_switch_name]
            if(len(vswitch) == 0):
                message = "cannot find vswitch %s" % vmnic_name
                self.logger.info(message)
                return message            
            
            vswitch = vswitch[0]
                
            vswitch_spec = vswitch.spec
            teaming_policy = vswitch_spec.policy.nicTeaming
            teaming_policy.rollingOrder = not failback_enabled
            network_system.UpdateVirtualSwitch(v_switch_name, vswitch_spec)
            
            message = "Failback is %s on %s" % ("enabled" if failback_enabled else "disabled", v_switch_name)
            self.logger.info(message)
            return message
         except Exception as e:
             self.logger.error(e)
             return e

    """
    Method to enable or disable network failover detection
    :param host_name: the host to configure
    :param v_switch_name:the virtual switch to configure
    :param net_failedover_detection_enabled: possible values are : LinkStatus, BeaconProbing
    """
    def set_network_failover_detection(self, host_name,v_switch_name, net_failedover_detection):
         try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network
            network_system = host.configManager.networkSystem
           
            vswitch = [vswitch for vswitch in network_config.vswitch if vswitch.name == v_switch_name]
            if(len(vswitch) == 0):
                message = "cannot find vswitch %s" % vmnic_name
                self.logger.info(message)
                return message            
            
            vswitch = vswitch[0]
                
            vswitch_spec = vswitch.spec
            teaming_policy = vswitch_spec.policy.nicTeaming
            if net_failedover_detection == "LinkStatus":
                teaming_policy.failureCriteria.checkBeacon = False
            elif net_failedover_detection == "BeaconProbing":
                teaming_policy.failureCriteria.checkBeacon = True
            else:
                message = "net_failedover_detection option not valid , use either LinkStatus or BeaconProbing"
                self.logger.info(message)
                return message            

            network_system.UpdateVirtualSwitch(v_switch_name, vswitch_spec)
            
            message = "Network failover detection is set to %s" % net_failedover_detection
            self.logger.info(message)
            return message
         except Exception as e:
             self.logger.error(e)
             return e.msg

    """
    Method to set the load balancing policy
    :param host_name: the host to configure
    :param v_switch_name:the virtual switch to configure
    :param LoadBalancingPolicy:possible values are loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit
    """
    def set_load_balancing_policy(self, host_name,v_switch_name, load_balancing_policy):
         try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network
            network_system = host.configManager.networkSystem
           
            vswitch = [vswitch for vswitch in network_config.vswitch if vswitch.name == v_switch_name]
            if(len(vswitch) == 0):
                message = "cannot find vswitch %s" % vmnic_name
                self.logger.info(message)
                return message            
            
            vswitch = vswitch[0]
                
            vswitch_spec = vswitch.spec
            teaming_policy = vswitch_spec.policy.nicTeaming
            teaming_policy.policy = load_balancing_policy
            network_system.UpdateVirtualSwitch(v_switch_name, vswitch_spec)
            
            message = "Load balancing policy is set to %s" % load_balancing_policy
            self.logger.info(message)
            return message
         except Exception as e:
             self.logger.error(e)
             return e.msg

    """
    Method to enable or disable traffic management on vnic
    :param host_name: host to configure
    :param port_group_name: port name to configure
    :param enable_management: True to enable management, False to disable management
    """
    def enable_disable_management_trafic(self, host_name, port_group_name,enable_management):
        try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network            
            virtual_nic_manager = host.configManager.virtualNicManager

            attached_vnic = [vnic for vnic in network_config.vnic if vnic.portgroup == port_group_name]
            if len(attached_vnic) > 0:
                attached_vnic = attached_vnic[0]
            else:
                attached_vnic = None

            if attached_vnic != None:
                device = attached_vnic.device
                
                if enable_management == True:
                    virtual_nic_manager.SelectVnic("management",device)
                    message = "Port group %s, management enabled on %s" % (port_group_name, device)
                else:
                    virtual_nic_manager.DeselectVnic("management",device)
                    message = "Port group %s, management disabled on %s" % (port_group_name, device)
                self.logger.info(message)
                return message
            else:
                message = "could not find nic for %s" % port_group_name
                self.logger.error(message)
                return message
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to set the notify switches option in nic teaming
    :param host_name: the host to configure
    :param v_switch_name:the virtual switch to configure
    :param notify_switches:possible values are loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit
    """
    def set_notify_switches(self, host_name,v_switch_name, notify_switches):
         try:
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return
                    
            network_config = host.config.network
            network_system = host.configManager.networkSystem
           
            vswitch = [vswitch for vswitch in network_config.vswitch if vswitch.name == v_switch_name]
            if(len(vswitch) == 0):
                message = "cannot find vswitch %s" % vmnic_name
                self.logger.info(message)
                return message            
            
            vswitch = vswitch[0]
                
            vswitch_spec = vswitch.spec
            teaming_policy = vswitch_spec.policy.nicTeaming
            teaming_policy.notifySwitches = True if notify_switches == True else False            
            network_system.UpdateVirtualSwitch(v_switch_name, vswitch_spec)
            
            message = "notify switches is set to %s" % notify_switches
            self.logger.info(message)
            return message
         except Exception as e:
             self.logger.error(e)
             return e.msg

    """
    Method to set nic teaming in port group
    :param host_name: the host to configure    
    :param v_port_group_name : the virtual port group to cofigure
    :param load_balancing_policy:possible values are loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit
    :param net_failedover_detections: possible values are LinkStatus and BeaconProbing
    :param notify_switches: True or False
    :param failback_enabled: sets the rolling order
    """
    def set_teaming_inheritance(self, host_name, v_port_group_name,
                                load_balancing_policy,
                                net_failedover_detections,
                                notify_switches,
                                failback_enabled):
            try:
                self.logger.info("getting port groups data from %s" % host_name)
                host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
                if host == None:
                     self.logger.error("could not find host %s", host_name)
                     return
             
                port_group = [pg for pg in host.config.network.portgroup if pg.spec.name == v_port_group_name]
                if len(port_group) > 0:
                    port_group = port_group[0]
                    port_group_spec = port_group.spec
                    nic_teaming = port_group_spec.policy.nicTeaming
                    nic_teaming.policy = load_balancing_policy
                    nic_teaming.notifySwitches = notify_switches
                    nic_teaming.rollingOrder = not failback_enabled
                    
                    nic_teaming.failureCriteria = self.vim.host.NetworkPolicy.NicFailureCriteria()
                    if net_failedover_detections == "LinkStatus":
                        nic_teaming.failureCriteria.checkBeacon = False
                    elif net_failedover_detections == "BeaconProbing":
                        nic_teaming.failureCriteria.checkBeacon = True
                   
                    host.configManager.networkSystem.UpdatePortGroup(v_port_group_name, port_group_spec)

                else:
                    message = "port group %s does not exist" % v_port_group_name
                    self.logger.error(message)
                    return message

                message = "set port group %s teaming data" % v_port_group_name
                self.logger.info(message)
                return message

            except Exception as e:
                self.logger.error(e)
                return e.msg

    """
    Method to enable or disable vmotion on port group
    :param host_name: the host to configure    
    :param v_port_group_name : the virtual port group to cofigure
    :enable_vmotion: True to enable vmotion False to disable vmotion
    """
    def enable_disable_vmotion(self, host_name, v_port_group_name, enable_vmotion):
        try:
            self.logger.info("Getting port groups data from %s" % host_name)
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                self.logger.error("could not find host %s", host_name)
                return

            vmotion_system = host.configManager.vmotionSystem
            network_config = host.config.network
            port_group = [pg for pg in network_config.portgroup if pg.spec.name == v_port_group_name]
            if len(port_group) > 0:
                port_group = port_group[0]                                   
            else:
                message = "port group %s does not exist" % v_port_group_name
                self.logger.error(message)
                return message

            attached_vnic = [vnic for vnic in network_config.vnic if vnic.portgroup == v_port_group_name]
            if len(attached_vnic) > 0:
                attached_vnic = attached_vnic[0]
            else:
                message = "vnic does not exist in %s" % v_port_group_name
                self.logger.error(message)
                return message
                
            if(enable_vmotion == True):                
                vmotion_system.SelectVnic(attached_vnic.device)     
                message = "Selected vnic %s for vmotion" % attached_vnic.device
            else:
                vmotion_system.DeselectVnic(attached_vnic.device)        
                message = "Deselected vnic %s for vmotion" % attached_vnic.device
            
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to set physical nic teaming policy for a virtual switch
    :param host_name: the host to configure 
    :param vswitch_name: the virtual switch on witch to configure the physical nic teaming policy
    :param pnic_name: the name of the physical nic
    :param nic_state: the state of the nic we want to set. Possible values: "Active", "Unused" or something else to set the nic state to Standby.
    """
    def set_nic_teaming_policy(self, host_name, vswitch_name, pnic_name, nic_state):
        try:
            self.logger.info("Setting nic '{0}' teaming policy to '{1}'. Host: '{2}', vSwitch: '{3}'".format(pnic_name, nic_state, host_name, vswitch_name))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)

            ns = host.configManager.networkSystem

            # find current spec object of given switch
            spec = None
            for vswitch in ns.networkConfig.vswitch:
                if vswitch.name == vswitch_name:
                    spec = vswitch.spec
                    break
            if spec is None:
                raise VmWareObjectNotFoundException(vswitch_name)
            
            # check if there is a pnic with pnic_name
            nic_exist = False
            for pnic in ns.networkConfig.pnic:
                if pnic.device == pnic_name:
                    nic_exist = True
                    break
            if not nic_exist:
                raise VmWareObjectNotFoundException(pnic_name)

            # check if pnic is on the vswitch
            if spec.bridge is None or pnic_name not in spec.bridge.nicDevice:
                raise Exception("Physical nic '{0}' is not set on virtual swtich '{1}'. Cannot update state.".format(pnic_name, vswitch_name))

            # update spec
            activeNicList = spec.policy.nicTeaming.nicOrder.activeNic
            standbyNicList = spec.policy.nicTeaming.nicOrder.standbyNic
            if nic_state == 'Active': 
                # Make NIC active
                if pnic_name in activeNicList:
                    self.logger.info("Nic '{0}' is already in active state".format(pnic_name))
                else:
                    activeNicList.append(pnic_name)
                if pnic_name in standbyNicList:
                    standbyNicList.remove(pnic_name)
            elif nic_state == 'Unused': 
                # Make NIC unused
                if pnic_name in activeNicList:
                    activeNicList.remove(pnic_name)
                elif pnic_name in standbyNicList:
                    standbyNicList.remove(pnic_name)
                else:
                    self.logger.info("Nic '{0}' is already unused".format(pnic_name))
            else: 
                # Make NIC standby
                if pnic_name in standbyNicList:
                    self.logger.info("Nic '{0}' is already in standby state".format(pnic_name))
                else:
                    standbyNicList.append(pnic_name)
                if pnic_name in activeNicList:
                    activeNicList.remove(pnic_name)
                
            # update configuration
            ns.UpdateVirtualSwitch(vswitchName = vswitch_name, spec = spec)

            message = "Configured nic teaming policy successfully"
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e

    """
    Method to manage a virutal switch. Method configures the properties: MTU and Number of Ports. If vSwtich doesnt exist method creates new switch on host.
    if pnic_name is provided and the physical network adapter is not set on the vSwtich method will add it.
    :param host_name: the host to configure 
    :param vswitch_name: the virtual switch to manage
    :param mtu: Value is int. The maximum transmission unit (MTU) of the virtual switch in bytes
    :param num_ports: Value is int. The number of ports that this virtual switch is configured to use. Changing this setting does not take effect until the next reboot. The maximum value is 1024, although other constraints, such as memory limits, may establish a lower effective limit.
    """
    def manage_vswitch(self, host_name, vswitch_name, pnic_name, mtu, num_ports):
        try:
            self.logger.info("Starting to manage vswitch. Host: '{0}', vSwitch: '{1}', pNic: '{2}', mtu: '{3}', num_ports: '{4}'".format(host_name, vswitch_name, pnic_name, mtu, num_ports))

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
            ns = host.configManager.networkSystem

            # find current spec object of given switch, if switch doest exist
            # create it
            spec = None
            add_new_vswitch = True
            for vswitch in ns.networkConfig.vswitch:
                if vswitch.name == vswitch_name:
                    spec = vswitch.spec
                    add_new_vswitch = False
                    break            
            
            if add_new_vswitch:
                # create new spec
                spec = self.vim.host.VirtualSwitch.Specification()

            # check if there is a pnic with pnic_name
            if pnic_name:
                nic_exist = False
                for pnic in ns.networkConfig.pnic:
                    if pnic.device == pnic_name:
                        nic_exist = True
                        break
                if not nic_exist:
                    raise VmWareObjectNotFoundException(pnic_name)
                # Set nic on vSwitch
                if spec.bridge is None:
                    spec.bridge = self.vim.host.VirtualSwitch.BondBridge()
                if pnic_name not in spec.bridge.nicDevice:
                    spec.bridge.nicDevice.append(pnic_name)
                else:
                    self.logger.info("Physical network adapter '{0}' is already set on virtual switch '{1}'".format(pnic_name, vswitch_name))               
            
            # update mtu & numofPorts in spec
            spec.mtu = int(mtu)
            spec.numPorts = int(num_ports)

            if add_new_vswitch:
                # create new vswitch
                self.logger.info("vSwitch '{0}' doest exist on host '{1}', adding new vSwitch".format(vswitch_name, host_name))
                ns.AddVirtualSwitch(vswitchName = vswitch_name, spec = None)
            else:
                # apply changes
                ns.UpdateVirtualSwitch(vswitchName = vswitch_name, spec = spec)

            return "Successfully updated vSwtich configurations"

        except Exception as e:
            self.logger.error(e)
            return e

    ###############################################
    #                  Storege #
    ###############################################
    
    """
    Method to retrive the storage devices canonical names
    :params host_name: the host from which to get the data
    """
    def get_canonical_names(self, host_name):
        try:
            self.logger.info("getting cannonical names")            
            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
        
            if host == None:
                    self.logger.error("could not find host %s", host_name)
                    return

            canonical_names = [lun.canonicalName for lun in host.config.storageDevice.scsiLun]

            return json.dumps(canonical_names)
        except Exception as e:
            self.logger.error(e)
            return e.msg


    """
    Method to upload file into the datastore
    :param vsphere_client_address: the vsphere client ip to connect to 
    :param data_center_name: the data store's datacenter
    :param data_store_name: the data store to upload the file to
    :local_file: the URI to the local file
    :remove_file: the name for the file to which will be created to updated on the datastore
    :disable_ssl_verification: should be false for now , otherwise this doesnt work
    """
    def upload_file_to_datastore(self, vsphere_client_address, data_center_name, data_store_name,local_file, remote_file,disable_ssl_verification):
        try:
            self.logger.info("uploading file to datastore")
                 
            client_cookie = self.si._stub.cookie
            cookie_name = client_cookie.split("=", 1)[0]
            cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
            cookie_path = client_cookie.split("=", 1)[1].split(";", 1)[1].split(";", 1)[0].lstrip()
            cookie_text = " " + cookie_value + "; $" + cookie_path
            
            # Make a cookie
            cookie = dict()
            cookie[cookie_name] = cookie_text
            
            params = {"dsName": data_store_name,"dcPath": data_center_name}
            
            if not remote_file.startswith("/"):
                remote_file = "/" + remote_file

            resource = "/folder" + remote_file
            http_url = "https://" + vsphere_client_address + ":443" + resource
            headers = {'Content-Type': 'application/octet-stream'}

            with open(local_file, "rb") as f:
                # Connect and upload the file
                request = requests.put(http_url,
                                       params=params,
                                       data=f,
                                       headers=headers,
                                       cookies=cookie,
                                       verify=disable_ssl_verification)
                if request.status_code == 201:
                    return "Success - new file created" 
                elif request.status_code in [200, 204]:
                    return "Success - existing file updated" 
                else:
                    return "Failed " + str(request.status_code)
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to upload file into the datastore
    :param vsphere_client_address: the vsphere client ip to connect to 
    :param data_center_name: the data store's datacenter
    :param data_store_name: the data store to upload the file to
    :local_file: the URI to the local file
    :remove_file: the name for the file to which will be created to updated on the datastore
    :disable_ssl_verification: should be false for now , otherwise this doesnt work
    """
    def delete_file_from_datastore(self, vsphere_client_address, data_center_name, data_store_name, remote_file,disable_ssl_verification):
        try:
            self.logger.info("uploading file to datastore")
                 
            client_cookie = self.si._stub.cookie
            cookie_name = client_cookie.split("=", 1)[0]
            cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
            cookie_path = client_cookie.split("=", 1)[1].split(";", 1)[1].split(";", 1)[0].lstrip()
            cookie_text = " " + cookie_value + "; $" + cookie_path
            
            # Make a cookie
            cookie = dict()
            cookie[cookie_name] = cookie_text
            
            params = {"dsName": data_store_name,"dcPath": data_center_name}
            
            if not remote_file.startswith("/"):
                remote_file = "/" + remote_file

            resource = "/folder" + remote_file
            http_url = "https://" + vsphere_client_address + ":443" + resource
            headers = {'Content-Type': 'application/octet-stream'}

            # Connect and upload the file
            request = requests.delete(http_url,
                                    params=params,
                                    headers=headers,
                                    cookies=cookie,
                                    verify=disable_ssl_verification)
            return "Success" if request.status_code in [201, 202, 204] else "Failed " + str(request.status_code)
        except Exception as e:
            self.logger.error(e)
            return e.msg


    ###############################################
    #                  VMS #
    ###############################################

    """
    Method to get details of all VMs
    """
    def get_vms(self):
        try:
            self.logger.info("Starting to get all VMs")
            result = []
            children = self.content.rootFolder.childEntity
            for child in children:
                if hasattr(child, 'vmFolder'):
                    datacenter = child
                else:
                    # some other non-datacenter type object
                    continue

                vm_folder = datacenter.vmFolder
                vm_list = vm_folder.childEntity
                for virtual_machine in vm_list:
                    self._search_vms_info(result, virtual_machine)

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to get status of virutal machine by name. More than one virtual machine can have the same name so method returns an array.
    :param vmname: the name of the virtual machine
    """
    def get_status(self, vmname):
        try:
            self.logger.info("Starting to get status of VM '{0}'".format(vmname))

            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)
            
            result = []

            for vm in vms:
                result.append(self._get_vm_info(vm))

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e.msg        

    """
    Method to get the guest id (guest OS). More than one virtual machine can have the same name so method returns an array.
    :param vmname: the name of the virtual machine
    """
    def get_vm_guest_os(self, vmname):
        try:
            self.logger.info("Starting to get guest OS of VM '{0}'".format(vmname))

            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)

            result = []

            for vm in vms:                    
                result.append({ "guestId" : vm.guest.guestId, "instanceUuid" : vm.config.instanceUuid })

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to get the VM tools version status
    :param vmname: the name of the virtual machine
    """
    def get_vm_tools_status(self, vmname):
        try:
            self.logger.info("Starting to get VM tools status for '{0}'".format(vmname))

            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)

            result = []

            for vm in vms:
                result.append({ 
                    "toolsVersionStatus" : vm.guest.toolsVersionStatus,
                    "instanceUuid" : vm.config.instanceUuid  })

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to update the VM tools.
    :param vmname: the name of the virtual machine
    """
    def update_vm_tools(self, vmname):
        try:
            self.logger.info("Starting to update VM tools for '{0}'".format(vmname))

            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)
            message = ""

            # get tools status for vm name
            vms_vmtools_status = json.loads(self.get_vm_tools_status(vmname))

            for vm in vms:
                # get the current status of the vm tools for current vm
                # instance
                vmtools_status = None
                for stat in vms_vmtools_status:
                    if stat["instanceUuid"] == vm.config.instanceUuid:
                        vmtools_status = stat
                        break
                
                # check if update is needed
                if vmtools_status["toolsVersionStatus"] != "guestToolsCurrent": 
                    try:
                        task = vm.UpgradeTools()                    
                        while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                            time.sleep(1)
                        if task.info.state == "error":
                            msg = "Error upgrading VM tools on '{0}' ({1}). {2}".format(vmname, vmtools_status["instanceUuid"], task.info.error.msg)
                            self.logger.error(msg)    
                            message += msg + "\n"
                    except Exception as exc:
                        msg = "Error upgrading VM tools on '{0}' ({1}). {2}".format(vmname, vmtools_status["instanceUuid"], exc.msg)
                        message += msg + "\n"          
                        self.logger.exception(exc)

                    msg = "Upgrading VM tools on '{0}' ({1}) complete".format(vmname, vmtools_status["instanceUuid"])
                    self.logger.info(msg)
                    message += msg + "\n"
                else:
                    msg = "VM tools are up to date on '{0}' ({1})".format(vmname, vmtools_status["instanceUuid"])
                    self.logger.info(msg)
                    message += msg + "\n"
                    
            return message.rstrip('\n ')

        except Exception as e:
            self.logger.exception(e)
            return e            

    """
    Method to get IP address of a specific VM
    :param vmname: the name of the virtual machine
    """
    def get_vm_ip(self, vmname):
        try:
            self.logger.info("Starting to get VM ip for '{0}'".format(vmname))

            vm = self.get_obj([self.vim.VirtualMachine], vmname)

            vm_info = self._get_vm_info(vm)

            result = { "name" : vm_info['name'], "ip" : vm_info['ip'] }

            return json.dumps(result)

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to set a VM to a specific state
    :param vmname: VM name to set a state
    :param state: the state to set. Posibble values are: 'powerOn', 'powerOff' and 'suspend'
    """
    def set_vm_state(self, vmname, state):
        try:
            self.logger.info("Starting to set VM '{0}' to state '{1}'".format(vmname, state))

            vm = self.get_obj([self.vim.VirtualMachine], vmname)
            
            if state == 'powerOn':
                return self.powerOn(vmname)
            elif state == 'powerOff':
                return self.powerOff(vmname)
            elif state == 'suspend':
                return self.suspend(vmname)

            raise ValueError("State '{0}' not supported".format(state))

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to set boot delay for a VM
    :param vmname: name of vitual machine
    :param start_delay: the boot delay to set in milliseconds 
    """        
    def set_vm_start_policy(self, vmname, start_delay):
        try:
            vm = self.get_obj([self.vim.VirtualMachine], vmname)

            cfg = self.vim.vm.ConfigSpec()
            cfg.bootOptions = self.vim.vm.BootOptions()
            cfg.bootOptions.bootDelay = start_delay

            task = vm.Reconfigure(cfg) 
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)

            if task.info.state == "error":
                message  = "Error reconfiguring {0} with start delay to {1} sec. {2}".format(vmname, start_delay, task.info.error.msg)
                self.logger.error(message)
                return message

            message = "Reconfiguring {0} with start delay to {1} ms completed".format(vmname, start_delay)
            self.logger.info(message)

            return message

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to set advanced (extra) config parametrs on Vm by name
    :param vmname: name of vitual machine
    :param key: The name of the advanced parameters to create/update
    :param value: The value of the advanced parameters
    """
    def set_vm_advanced_parameters(self, vmname, key, value):
        try:
            self.logger.info("Starting to set advanced parameters on VM '{0}'".format(vmname))

            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)
            message = ""
            for vm in vms:
                opt = self.vim.option.OptionValue()
                opt.key = key
                opt.value = value
                spec = self.vim.vm.ConfigSpec()
                spec.extraConfig = []
                spec.extraConfig.append(opt)
                task = vm.ReconfigVM_Task(spec)
                while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                    time.sleep(1)

                if task.info.state == "error":
                    msg = "Error setting advanced parameter on VM '{0}' ({1})".format(vmname, vm.config.instanceUuid)
                    self.logger.error(msg)
                    message += msg + "\n"

                msg = "Setting advanced parameter completed"
                self.logger.error(msg)
                message += msg + "\n"

            return message.rstrip('\n ')

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    :param vmname: name of vitual machine
    :param parameter: Indicates what config parameter to update. '0' - Update size of virtual machines memory, MB. '1' - Update number of virtual processors in a virtual machine
    :param parameter_value: numberic value for the parameter that is updated
    """
    def set_vm(self, vmname, parameter, parameter_value):
        try:
            self.logger.info("Starting to update VM settings '{0}'".format(vmname))

            if parameter not in ['0', '1']:
                raise ValueError("Parameter value is not supported")

            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)
            message = ""
            for vm in vms:
                spec = self.vim.vm.ConfigSpec()
                if parameter == '0':
                    parameter_text = "memory"
                    spec.memoryMB = long(parameter_value)
                else:
                    parameter_text = "number of CPUs"
                    spec.numCPUs = int(parameter_value)
                task = vm.ReconfigVM_Task(spec)
                while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                    time.sleep(1)

                if task.info.state == "error":
                    msg = "Error updating {2} on VM '{0}' ({1})".format(vmname, vm.config.instanceUuid, parameter_text)
                    self.logger.error(msg)
                    message += msg + "\n"
                else:
                    msg = "Updating VM '{0}' ({1}) to '{2}':{3} completed".format(vmname, vm.config.instanceUuid, parameter_text, parameter_value)
                    self.logger.info(msg)
                    message += msg + "\n"

            return message.rstrip('\n ')

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to configure the network interface of a guest with static IP address and static dns servers
    :param vmname: name of vitual machine
    :param vmguest_user: user name to use to login to guest using VM Tools
    :param vmguest_pwd: password to use to login to guest using VM Tools
    :param ip_address: static IP address to set on guest
    :param subnet_mask: subnet mask to set on guest
    :param gateway: gateway to set on guest
    :param dns_primary: primary dns to set on guest (optional)
    :param dns_secondary: secondary dns to set on guest (optional). If secondary dns is provided than primary dns is mandatory.
    """
    def set_vm_nic(self, vmname, vmguest_user, vmguest_pwd, ip_address, subnet_mask, gateway, dns_primary, dns_secondary):
        try:
            vms = self.get_obj_all_byname([self.vim.VirtualMachine], vmname)
            message = ""

            for vm in vms:
                # check VM Tools are OK
                tools_status = vm.guest.toolsStatus
                if tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning':
                    msg = "VM Tools is either not running or not installed on VM '{0}' ({1}). ".format(vmname, vm.config.instanceUuid) + \
                            "Rerun the script after verifying that VMWareTools is running."
                    self.logger.error(msg)
                    return (message + msg).rstrip('\n ')

                # check guest OS is supported
                guest_os = vm.guest.guestId
                if guest_os == "windows7Server64Guest" or guest_os == "windows7_64Guest":
                    interface_name = "Local Area Connection"
                elif guest_os == "windows8Server64Guest":
                    interface_name = "Ethernet"
                else:
                    msg = "Guest OS '{0}' found on VM '{1}' ({2}) is not currently supported.".format(guest_os, vmname, vm.config.instanceUuid)
                    self.logger.error(msg)
                    return (message + msg).rstrip('\n ')

                # create guest credentials object
                creds = self.vim.vm.guest.NamePasswordAuthentication(username=vmguest_user, password=vmguest_pwd)

                # run cmd to configure ip address and gateway
                pid_ipaddress = self._exec_cmd_guest_windows(vm, creds, 
                    "netsh interface ip set address name=\"{0}\" static {1} {2} {3}".format(interface_name, ip_address, subnet_mask, gateway))                

                pid_dns_primary = None
                pid_dns_secondary = None
                if dns_primary:
                    # run cmd to configure primary dns servers
                    pid_dns_primary = self._exec_cmd_guest_windows(vm, creds,
                        "netsh interface ip set dns name=\"{0}\" source=static address={1} primary".format(interface_name, dns_primary))
                if dns_primary and dns_secondary:
                    # run cmd to configure primary dns servers
                    pid_dns_secondary = self._exec_cmd_guest_windows(vm, creds,
                        "netsh interface ip add dns name=\"{0}\" address={1} index=2".format(interface_name, dns_secondary))

                # wait until process finishes
                exitCode = self._wait_for_process(vm, creds, pid_ipaddress)
                msg = "IP Address configured successfully. " if exitCode is 0 else "Failed to configured IP Address. "

                if pid_dns_primary is not None:
                    exitCode = self._wait_for_process(vm, creds, pid_dns_primary)
                    msg += "Primary DNS configured successfully. " if exitCode is 0 else "Failed to configure primary DNS. "
                
                if pid_dns_secondary is not None:
                    exitCode = self._wait_for_process(vm, creds, pid_dns_secondary)
                    msg += "Secondary DNS configured successfully. " if exitCode is 0 else "Failed to configure secondary DNS. "

                self.logger.info(msg)
                message += msg + "\n"

            return message.rstrip('\n ')

        except Exception as e:
            self.logger.exception(e)
            return e.msg

    """
    Method to add a hard disk  to a vm
    :param host_name: the host to configure
    :data_center_name: the datacenter to configure
    :storage_name: the storage to configure
    :hd_capacity_GB: the new hard disk capacity in GB
    :disk_file_path: the hard disk file name in the datastore
    """
    def add_harddisk_to_vm(self,host_name,data_center_name, storage_name, vm_name, hd_capacity_GB,disk_file_path):
        try:
            self.logger.info("adding hard disk to %s" % vm_name)
            vm = self.get_obj([self.vim.VirtualMachine], vm_name)
            datacenter = self.get_obj([self.vim.Datacenter], data_center_name)
            number_of_ide_slots = 2

            if(vm == None):
                message = "cannot find vm %s" % (vm_name)
                self.logger.error(message)
                return message

            if(datacenter == None):
                message = "cannot find datacenter %s" % data_center_name
                self.logger.error(message)
                return message

            unused_ide_controllers = [vd for vd in vm.config.hardware.device if isinstance(vd, self.vim.vm.device.VirtualIDEController) and len(vd.device) < number_of_ide_slots]
            if(unused_ide_controllers == None or len(unused_ide_controllers) == 0):
                message = "there are no unused IDE controllers"
                self.logger.error(message)
                return message

            unused_controller = unused_ide_controllers[0]
            controller_key = unused_controller.key
            unit_number = len(unused_controller.device)            
            vd_path = disk_file_path

            spec = self.vim.VirtualDiskManager.FileBackedVirtualDiskSpec()
            spec.diskType = self.vim.VirtualDiskManager.VirtualDiskType().thick
            spec.adapterType = self.vim.VirtualDiskManager.VirtualDiskAdapterType().ide
            spec.capacityKb = hd_capacity_GB * 1024 * 1024
            task = self.si.content.virtualDiskManager.CreateVirtualDisk(vd_path, datacenter,spec)
            
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)

            if task.info.state == "error":
                message = task.info.error.msg
                self.logger.error(message)
                return message

                
            vd_path = task.info.result
           
            cfg = self.vim.vm.ConfigSpec()
            cfg.deviceChange = [self.vim.vm.device.VirtualDeviceSpec()]       
            cfg.deviceChange[0].operation = self.vim.vm.device.VirtualDeviceSpec.Operation().add   
            cfg.deviceChange[0].device = self.vim.vm.device.VirtualDisk() 
            cfg.deviceChange[0].device.controllerKey = controller_key
            cfg.deviceChange[0].device.unitNumber = unit_number
            cfg.deviceChange[0].device.backing = self.vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            cfg.deviceChange[0].device.backing.diskMode = "persistent"            
            cfg.deviceChange[0].device.backing.fileName = vd_path          
            task = vm.Reconfigure(cfg)
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)

            if task.info.state == "error":                
                message = task.info.error.msg
                self.logger.error(message)

                try:
                    self.si.content.virtualDiskManager.DeleteVirtualDisk(vd_path, datacenter) #rollback
                except Exception as e:                    
                    self.logger.error("unable to rollback add hardisk, please delete the file manually at %s" % vd_path)                    
                return message

            return "success"
        except Exception as e:
            self.logger.error(e);
            return e.msg



    """
    Method to delete virtual machine
    :param vm_name: the virtual machine to delete
    """
    def delete_vm(self, vm_name):
        try:
            # self.logger.info("Deleting vm %s" % vm_name)
            vm = self.get_obj([self.vim.VirtualMachine], vm_name)
            
            if(vm == None):
                message = "cannot find vm %s" % (vm_name)
                # self.logger.error(message)
                return message

            if vm.runtime.powerState != "poweredOff":
                task = vm.PowerOff()

                while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                    time.sleep(1)

                if task.info.state == "error":                
                    message = task.info.error.msg
                    # self.logger.error(message)
                    return message

            task = vm.Destroy()
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":                
                message = task.info.error.msg
                # self.logger.error(message)
                return message

            return "success"
        except Exception as e:
            # self.logger.error(e)
            return e.message

    """
    Method to deploy OVF
    :param ovf_file_path: path to ovf file
    :param host_name: host to configure
    :param data_center_name: the datacenter to add the new ovf
    :param data_store_name:the datastore name to host the new ovf
    :param new_name: the new name for the ovf
    """
    def deploy_ovf(self, ovf_file_path, host_name, data_center_name, data_store_name, new_name):
        try:            
            self.logger.info("deploying OVF")
            f = open(ovf_file_path, 'r')
            ovfd = f.read()
            f.close()

            host = self.content.searchIndex.FindByDnsName(dnsName = host_name, vmSearch = False)
            if(host == None):
                message = "could not find host %s" % host_name
                self.logger.error(message)
                return message
                                    
            datacenter = self.get_obj([self.vim.Datacenter], data_center_name)
            datastore = self.get_obj([self.vim.Datastore], data_store_name)

            if(datacenter == None):
                message = "could not find datacenter %s" % datacenter
                self.logger.error(message)
                return message

            if(datastore == None):
                message = "could not find datastore %s" % datastore
                self.logger.error(message)
                return message

            resource_pool = datacenter.hostFolder.childEntity[0].resourcePool

            # Now we create the import spec
            manager = self.si.content.ovfManager
            isparams = self.vim.OvfManager.CreateImportSpecParams()
            isparams.entityName = new_name
            import_spec = manager.CreateImportSpec(ovfd, resource_pool, datastore, isparams)
            lease = resource_pool.ImportVApp(import_spec.importSpec, datacenter.vmFolder, host)

            def keep_lease_alive(lease):
                  while(True):
                    time.sleep(5)
                    try:
                      # This keeps the lease alive.
                      lease.HttpNfcLeaseProgress(50)
                      if (lease.state == self.vim.HttpNfcLease.State.done):
                        return
                    # If the lease is released, we get an exception.
                    except:
                      return

            while(True):
                  if (lease.state == self.vim.HttpNfcLease.State.ready):
                        keepalive_thread = threading.Thread(target=keep_lease_alive,args=(lease,))
                        keepalive_thread.daemon = True
                        keepalive_thread.start()
                        lease.HttpNfcLeaseComplete()
                        keepalive_thread.join()
                        return 0
                  elif (lease.state == self.vim.HttpNfcLease.State.error):
                        message = "error with lease state, check vcenter logs"
                        self.logger.error(message)
                        return message
        except Exception as e:
            self.logger.error(e)
            return e.message

    """
    Method to set the virtual cd-rom ISO path
    :param datastore_name: the name of the datastore that holds the ISO file
    :param vm_name: the name of the vm to reconfigure
    :param iso_path: the ISO file relative path in the datastore
    """
    def mount_iso_to_cd(self,datastore_name,vm_name, iso_path):
        try:
            self.logger.info("mounting cd")
            
            vm = self.get_obj([self.vim.VirtualMachine], vm_name)
            if vm == None:
                message = "Could not find vm %s" % vm_name
                self.logger.error(message)
                return message
            
            virtual_cd = [vd for vd in vm.config.hardware.device if isinstance(vd, self.vim.vm.device.VirtualCdrom)]
            if(virtual_cd != None and len(virtual_cd) > 0):
                virtual_cd = virtual_cd[0]
            else:
                message = "vm % has no virtual cd" % vm_name
                self.logger.error(message)
                return message

            datastore_file_path = "[%s] %s" % (datastore_name,iso_path)
            
            cfg = self.vim.vm.ConfigSpec()
            cfg.deviceChange = [self.vim.vm.device.VirtualDeviceSpec()]       
            cfg.deviceChange[0].operation = self.vim.vm.device.VirtualDeviceSpec.Operation().edit
            cfg.deviceChange[0].device = self.vim.vm.device.VirtualCdrom() 
            cfg.deviceChange[0].device.key = virtual_cd.key
            cfg.deviceChange[0].device.controllerKey = virtual_cd.controllerKey
            cfg.deviceChange[0].device.backing = self.vim.vm.device.VirtualCdrom.IsoBackingInfo()            
            cfg.deviceChange[0].device.backing.fileName = datastore_file_path          
            task = vm.Reconfigure(cfg)
            
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":                
                message = task.info.error.msg
                self.logger.error(message)
                return message
                                
            return "success"

        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to set the network adapter label
    :param vm_name:the vm  to reconfigure    
    :param virtual_nic: the virtual network card to reconfigure
    :param network_adapter_new_label: the new network to set on the nic
    """
    def set_network_adapter_label(self,vm_name,network_adapter_name, network_adapter_new_label):
        try:
            self.logger.info("setting %s network adapter label" % vm_name)
            
            vm = self.get_obj([self.vim.VirtualMachine], vm_name)
            if vm == None:
                message = "Could not find vm %s" % vm_name
                self.logger.error(message)
                return message

            virtual_nic = [device for device in vm.config.hardware.device if device.deviceInfo.label == network_adapter_name]
            if virtual_nic == None or len(virtual_nic) == 0:
                message = "Could not find virtual nic %s" % virtual_nic
                self.logger.error(message)
                return message
            else:
                virtual_nic = virtual_nic[0]

            cfg = self.vim.vm.ConfigSpec()
            cfg.deviceChange = [self.vim.vm.device.VirtualDeviceSpec()]       
            cfg.deviceChange[0].operation = self.vim.vm.device.VirtualDeviceSpec.Operation().edit
            cfg.deviceChange[0].device = virtual_nic                                       
            cfg.deviceChange[0].device.backing.deviceName = network_adapter_new_label                           
            task = vm.Reconfigure(cfg)

            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":                
                message = task.info.error.msg
                self.logger.error(message)
                return message

            return "success"
        except Exception as e:
            self.logger.error(e)
            return e.msg

    """
    Method to enable remote connection on windows servers
    """
    def enable_remote_connections(self, vm_name,vmguest_user,vmguest_pwd):
        try:
            self.logger.info("enabling remote connection on %s" % vm_name)
            vm = self.get_obj([self.vim.VirtualMachine], vm_name)
            
            if vm is None:
                message = "Could not find a vm called %s" % vm_name
                self.logger.error(message)
                return message

            # check VM Tools are OK
            tools_status = vm.guest.toolsStatus
            if tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning':
                msg = "VM Tools is either not running or not installed on VM '{0}' ({1}). ".format(vm_name, vm.config.instanceUuid) + \
                        "Rerun the script after verifying that VMWareTools is running."
                self.logger.error(msg)
                message = msg + "\n"

            creds = self.vim.vm.guest.NamePasswordAuthentication(username=vmguest_user, password=vmguest_pwd)
            pid_ipaddress = self._exec_cmd_guest_windows(vm, creds,"winrm quickconfig -quiet")
            exitCode = self._wait_for_process(vm, creds, pid_ipaddress)
            message = "Remote connections enabled successfully" if exitCode is 0 else "Failed to enable remote connections"
            self.logger.info(message)
            return message

        except Exception as e:
            self.logger.error(e)
            return e.msg

    ###############################################
    #           PRIVATE HELPER METHODS #
    ###############################################

    """
    PRIVATE METHOD - Check recursively if host is in location
    :param host: host/container object
    :param location: container name
    """
    def _is_host_in_location(self, host, location):
        if host.parent is None:
            return False

        if host.parent.name == location:
            return True

        return self._is_host_in_location(host.parent, location)

    """
    PIVATE METHOD: Get information for a particular virtual machine or recurse into a
    folder with depth protection (maxdepth=20)
    :param vm_info_list: list that saves the info of each vm
    :param virtual_machine: virtual machine object or folder object
    :param depth: current depth
    """
    def _search_vms_info(self, vm_info_list, virtual_machine, depth=1):
        maxdepth = 20
        # if this is a group it will have children.  if it does, recurse into
        # them
        # and then return
        if hasattr(virtual_machine, 'childEntity'):
            if depth > maxdepth:
                return
            vmList = virtual_machine.childEntity
            for c in vmList:
                self._search_vms_info(vm_info_list, c, depth + 1)
            return

        vm_info_list.append(self._get_vm_info(virtual_machine))

    """
    PIVATE METHOD: Get info for a single vm
    :param virtual_machine: virtual machine object
    """
    def _get_vm_info(self, virtual_machine):
        summary = virtual_machine.summary
        memorySizeGB = 0
        if summary.config.memorySizeMB:
            memorySizeGB = round(summary.config.memorySizeMB / 1024, 3)
        ip_address = None
        if summary.guest is not None:
            ip_address = summary.guest.ipAddress
        return { "name" : summary.config.name,
                "path" : summary.config.vmPathName,
                "guest" : summary.config.guestFullName,
                "instanceUUID" : summary.config.instanceUuid,
                "memorySizeGB" : memorySizeGB,
                "numCpu" : summary.config.numCpu,
                "state" : summary.runtime.powerState,
                "ip" : ip_address }

    def get_vm_info(self, vm_name):
        vm = self.get_obj([self.vim.VirtualMachine], vm_name)
        return self._get_vm_info(vm)

    # run a command on Guest VM using VM Tools and return the PID of the newly
    # created process
    def _exec_cmd_guest(self, vm, creds, cmd, args):
        cmdSpec = self.vim.vm.guest.ProcessManager.ProgramSpec(programPath = cmd, arguments = args)
        return self.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=creds, spec=cmdSpec)

    def _exec_cmd_guest_windows(self, vm, creds, args):
        return self._exec_cmd_guest(vm, creds,"\Windows\System32\cmd.exe", "/c " + args)
    
    # wait until process with PID finishes and return exit code.  Raise
    # exception if reached timeout
    def _wait_for_process(self, vm, creds, pid, timeout=15):
        pm = self.content.guestOperationsManager.processManager
        proc_info = pm.ListProcesses(vm=vm, auth=creds, pids=[pid])[0]
        counter = 0
        while proc_info.endTime is None and counter < timeout:
            time.sleep(1)
            counter += 1
            proc_info = pm.ListProcesses(vm=vm, auth=creds, pids=[pid])[0]
        if proc_info.endTime is not None:
            return proc_info.exitCode 
        raise Exception("Timeout reached while waiting for process on guest to end")

    def wait_task(self, task):
        while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
            time.sleep(1)

        if task.info.state == "error":            
            self.logger.error(task.info.error.msg)
                        
        return task.info
    def create_snapshot(self, typed_moref, snapshot_name, snapshot_description):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + typed_moref)
        vm._stub = si._stub

        desc = None
        if snapshot_description:
            desc = snapshot_description

        task = vm.CreateSnapshot_Task(name=snapshot_name,
                                      description=desc,
                                      memory=True,
                                      quiesce=False)


        print("Snapshot Completed.")

    def get_list_of_snapshots(self, typed_moref):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + typed_moref)
        vm._stub = si._stub
        snap_info = vm.snapshot
        list_of_snapshots = []
        if (snap_info != None):
            list_of_snapshots.append(str(snap_info.rootSnapshotList[0].snapshot).strip("'"))
            childSnapshot = snap_info.rootSnapshotList[0]
            while(childSnapshot.childSnapshotList):
                list_of_snapshots.append(str(childSnapshot.childSnapshotList[0].snapshot).strip("'"))
                childSnapshot = childSnapshot.childSnapshotList[0]
        return list_of_snapshots

    def get_list_of_snapshots_by_name(self, vm_name):
        si = self.si
        vm = self.get_obj([self.vim.VirtualMachine], vm_name)
        # vm._stub = si._stub
        snap_info = vm.snapshot
        list_of_snapshots = []
        if(snap_info != None):
            list_of_snapshots.append(str(snap_info.rootSnapshotList[0].name).strip("'"))
            childSnapshot = snap_info.rootSnapshotList[0]
            while(childSnapshot.childSnapshotList):
                list_of_snapshots.append(str(childSnapshot.childSnapshotList[0].name).strip("'"))
                childSnapshot = childSnapshot.childSnapshotList[0]
        return list_of_snapshots

    def delete_snapshot(self, typed_moref):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        snapshot = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if snapshot is None:
            raise SystemExit("Unable to find Snapshot " + typed_moref)
        snapshot._stub = si._stub
        snapshot.RemoveSnapshot_Task(removeChildren=False)
        print("Snapshot " + typed_moref + " removed.")

    def restore_from_snapshot(self, typed_moref):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        snapshot = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if snapshot is None:
            raise SystemExit("Unable to find Snapshot " + typed_moref)
        snapshot._stub = si._stub
        snapshot.RevertToSnapshot_Task()
        print("Restored vm to snapshot " + typed_moref)

    def add_disk(self, vm_typed_moref, disk_size, disk_type):
        si = self.si
        typed_moref_elems = vm_typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + vm_typed_moref)
        vm._stub = si._stub
        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        for dev in vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    raise SystemExit("we don't support this many disks")
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
        # add disk here
        dev_changes = []
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if disk_type == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)
        spec.deviceChange = dev_changes
        vm.ReconfigVM_Task(spec=spec)
        print "%sGB disk added to %s" % (disk_size, vm.config.name)

    """
        Method to remove a hard disk from VM and delete the vdmk file from the datastore
        :param host_name: the host to configure
        :data_center_name: the datacenter to configure
        :storage_name: the storage to configure
        :disk_file_path: the disk's file path in the storage
        """
    def remove_harddisk_from_vm(self,data_center_name, vm_name, disk_file_path):
        try:
            self.logger.info("removing hard disk to %s" % vm_name)
            vm = self.get_obj([self.vim.VirtualMachine], vm_name)
            datacenter = self.get_obj([self.vim.Datacenter], data_center_name)

            if(vm == None):
                message = "cannot find vm %s" %(vm_name)
                raise SystemExit(message)
                # self.logger.error(message)
                # return message

            if(datacenter == None):
                message = "cannot find datacenter %s" % data_center_name
                raise SystemExit(message)
                # self.logger.error(message)
                # return message

            # find the disk we want to remove
            vd_key = None
            for vd in vm.config.hardware.device:
                if type(vd) is self.vim.VirtualDisk:
                    if vd.backing.fileName == disk_file_path:
                        vd_key = vd.key

            if(vd_key == None):
                message = "cannot find virtual disk to delete '%s'" % disk_file_path
                raise SystemExit(message)
                # self.logger.error(message)
                # return message

            # delete virtual disk device from the VM
            cfg = self.vim.vm.ConfigSpec()
            cfg.deviceChange =[self.vim.vm.device.VirtualDeviceSpec()]
            cfg.deviceChange[0].operation = self.vim.vm.device.VirtualDeviceSpec.Operation().remove
            cfg.deviceChange[0].device = self.vim.vm.device.VirtualDisk()
            cfg.deviceChange[0].device.key = vd_key
            task = vm.Reconfigure(cfg)
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":
                message = task.info.error.msg
                raise SystemExit(message)
                # self.logger.error(message)
                # return message

            # delete the virtual disk associated with the virtual device
            task = self.si.content.virtualDiskManager.DeleteVirtualDisk(disk_file_path, datacenter)
            while task.info.state not in [self.vim.TaskInfo.State.success, self.vim.TaskInfo.State.error]:
                time.sleep(1)
            if task.info.state == "error":
                message = task.info.error.msg
                raise SystemExit(message)
                # self.logger.error(message)
                # return message
            print "Successfully deleted the hard drive " + disk_file_path
            return "success"
        except Exception as e:
            self.logger.error(e);
            return e.msg

    def add_network_interface(self, vm_typed_moref, adapter_type, network_moref ):
        si = self.si
        typed_moref_elems = vm_typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + vm_typed_moref)
        vm._stub = si._stub

        typed_moref_elems = network_moref.split(':')
        network_obj = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if network_obj is None:
            raise SystemExit("Unable to find Network " + network_moref)
        network_obj._stub = si._stub

        spec = vim.vm.ConfigSpec()
        dev_changes = []
        network_interface_spec = vim.vm.device.VirtualDeviceSpec()
        network_interface_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        # network_interface_spec.device = vim.vm.device.VirtualEthernetCard()
        nictype2device = {
            "pcnet": vim.vm.device.VirtualPCNet32(),
            "e1000": vim.vm.device.VirtualE1000(),
            "vmxnet2": vim.vm.device.VirtualVmxnet2(),
            "vmxnet3": vim.vm.device.VirtualVmxnet3(),
        }
        if adapter_type not in nictype2device:
            raise SystemExit('Unknown adapter type ' + adapter_type)
        network_interface_spec.device = nictype2device[adapter_type]
        network_interface_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        network_interface_spec.device.backing.deviceName = network_obj.name
        dev_changes.append(network_interface_spec)
        spec.deviceChange = dev_changes
        if(vm.ReconfigVM_Task(spec=spec)):
            print "Network interface has been successfully added"

    def remove_network_interface(self, vm_typed_moref, adapter_key):
        si = self.si
        typed_moref_elems = vm_typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + vm_typed_moref)
        vm._stub = si._stub

        spec = vim.vm.ConfigSpec()
        dev_changes = []
        network_interface_spec = vim.vm.device.VirtualDeviceSpec()
        network_interface_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        device = None
        for d in vm.config.hardware.device:
            if d.key == adapter_key:
                device = d
        if device == None:
            raise SystemExit("No device with adapter_key " + str(adapter_key))
        network_interface_spec.device = device
        dev_changes.append(network_interface_spec)
        spec.deviceChange = dev_changes
        task = vm.ReconfigVM_Task(spec=spec)
        print "Network interface " + device.deviceInfo.label + " has been removed"

    def add_dvportgroup_to_dvswitch(self, dvswitch_typed_moref, name, number_of_ports, portgroup_type, vlan_type, vlan_details, allow_promiscuous_mode=False):
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
        if (not p.match(str(vlan_details))) :
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
        dvsPortConfig.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
        dvsPortConfig.securityPolicy.allowPromiscuous = vim.BoolPolicy()
        dvsPortConfig.securityPolicy.allowPromiscuous.value = allow_promiscuous_mode
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

    def clone_vm(self, vm_typed_moref, name):
        si = self.si
        typed_moref_elems = vm_typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + vm_typed_moref)
        vm._stub = si._stub
        # appending number to the VM name if VM with such name already exists
        target_vm = None
        try:
            target_vm = self.get_obj([self.vim.VirtualMachine],name)
        except Exception as e:
            pass
        i = 1
        while (target_vm != None):
            try:
                name_with_index = name + str(i)
                target_vm = self.get_obj([self.vim.VirtualMachine],name_with_index)
                i = i + 1
            except Exception as e:
                name = name_with_index
                break

        spec = vim.vm.CloneSpec()
        spec.template = False
        spec.powerOn = False
        spec.location = vim.vm.RelocateSpec()
        # spec.location.datastore = folder.parent
        if(vm.CloneVM_Task(vm.parent, name, spec=spec)):
            print "Virtual machine " + vm.name + " has been successfully cloned to the machine " + name

    def convert_to_template(self, vm_typed_moref):
        si = self.si
        typed_moref_elems = vm_typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + vm_typed_moref)
        vm._stub = si._stub

        if(vm.MarkAsTemplate()):
            print "Virtual machine " + vm.name + "has been successfully converted to template"

    def get_allocation_info(self, vm_typed_moref):
        si = self.si
        typed_moref_elems = vm_typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + vm_typed_moref)
        vm._stub = si._stub

        allocation_data = vm.layoutEx
        taken_storage = vm.summary.storage.committed
        all_storage = vm.summary.storage.uncommitted
        unshared = vm.summary.storage.unshared

    def get_allocation_info_for_datastores(self):
        datacenter_typed_moref = "vim.Datacenter:datacenter-2"
        si = self.si
        typed_moref_elems = datacenter_typed_moref.split(':')
        datacenter = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if datacenter is None:
            raise SystemExit("Unable to find datacenter " + datacenter_typed_moref)
        datacenter._stub = si._stub

        allocation_data_dict = {}
        for datastore in datacenter.datastore:
            # capability = datastore.capability
            # capacity = datastore.summary.capacity
            freeSpace = datastore.summary.freeSpace
            allocation_data_dict[datastore.name] = str(freeSpace / 1024 / 1024 / 1024) + "GB"
        print allocation_data_dict

class fake_service(object):
    def get_property(self, dvpg, propname):
        if propname == 'summary':
            return dvpg.summary
        if propname == 'config':
            return dvpg.config
