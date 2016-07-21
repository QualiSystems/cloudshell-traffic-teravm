class NetworkInterfaceFunctions:
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