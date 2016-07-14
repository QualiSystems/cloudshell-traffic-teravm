from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
from cloudshell.traffic.teravm.app_deployment_handler import AppDeploymentHandler


class DeployTeraVM(ResourceDriverInterface):
    def __init__(self):
        bootstrap = DriverBootstrap()
        bootstrap.initialize()
        self.handler = AppDeploymentHandler()

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def Deploy(self, context, Name=None):
        """ Deploys a TeraVM entity - a controller or a test module

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type Name: str
        """
        self.handler.deploy(context, Name)


