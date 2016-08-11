from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context_utils import context_from_args
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
from cloudshell.traffic.teravm.test_module.driver_handler import TestModuleHandler


class TeraVMTestModuleDriver(ResourceDriverInterface):
    def __init__(self):
        bootstrap = DriverBootstrap()
        bootstrap.initialize()
        self.handler = TestModuleHandler()

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    @context_from_args
    def get_inventory(self, context):
        """ Returns device resource, sub-resources and attributes

        :type context: cloudshell.shell.core.driver_context.AutoLoadCommandContext
        :rtype: cloudshell.shell.core.driver_context.AutoLoadDetails
        """
        return self.handler.get_inventory(context)

    @context_from_args
    def connect_child_resources(self, context):
        """ Takes connectors to app and reconnects them

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :rtype: str
        """
        return self.handler.connect_child_resources(context)
