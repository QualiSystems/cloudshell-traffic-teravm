from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.traffic.teravm.management_assistant.tvm_ma import TeraVMManagementAssistantHandler
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
from cloudshell.shell.core.context_utils import context_from_args


class TeraVMManagementAssistant(ResourceDriverInterface):
    def __init__(self):
        bootstrap = DriverBootstrap()
        bootstrap.initialize()
        self.handler = TeraVMManagementAssistantHandler()

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    @context_from_args
    def deploy_tvm(self, context, request):
        return self.handler.deploy_tvm(context, request)


