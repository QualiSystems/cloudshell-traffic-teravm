class HardDiskFunctions:
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
