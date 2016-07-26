import cloudshell.traffic.teravm.common.i18n as c


class TVMMAModel:
    def __init__(self, esxi_host, datastore, management_network, comms_network, host_address, vm_location,
                 holding_network):
        self._esxi_host = esxi_host
        self._datastore = datastore
        self._management_network = management_network
        self._comms_network = comms_network
        self._host_address = host_address
        self._vm_location = vm_location
        self._holding_network = holding_network

    @classmethod
    def from_dict(cls, tvmma_details, host_address):
        return cls(tvmma_details[c.ATTRIBUTE_NAME_ESXI_HOST],
                   tvmma_details[c.ATTRIBUTE_NAME_DATASTORE],
                   tvmma_details[c.ATTRIBUTE_NAME_MANAGEMENT_NETWORK],
                   tvmma_details[c.ATTRIBUTE_NAME_COMMS_NETWORK],
                   host_address,
                   tvmma_details[c.ATTRIBUTE_NAME_VM_LOCATION],
                   tvmma_details[c.ATTRIBUTE_NAME_HOLDING_NETWORK])

    @classmethod
    def from_context(cls, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :rtype: cloudshell.traffic.teravm.models.tvm_ma_model.TVMMAModel
        """
        return cls.from_dict(context.resource.attributes, context.resource.address)

    @property
    def esxi_host(self):
        return self._esxi_host

    @property
    def datastore(self):
        return self._datastore

    @property
    def management_network(self):
        return self._management_network

    @property
    def comms_network(self):
        return self._comms_network

    @property
    def host_address(self):
        return self._host_address

    @property
    def vm_location(self):
        return self._vm_location

    @property
    def holding_network(self):
        return self._holding_network
