from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.traffic.teravm.management_assistant.tvm_ma import TeraVMManagementAssistantHandler
from debug_utils import debugger


class TeraVMManagementAssistant(ResourceDriverInterface):
    def __init__(self):
        self.handler = TeraVMManagementAssistantHandler()

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def deploy_tvm(self, context, request):
        debugger.attach_debugger()
        return self.handler.deploy_tvm(context, request)


