from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
from cloudshell.traffic.teravm.deployment.app_deployment_handler import AppDeploymentHandler
from cloudshell.shell.core.context_utils import context_from_args


class DeployTeraVM(ResourceDriverInterface):
    def __init__(self):
        bootstrap = DriverBootstrap()
        bootstrap.initialize()
        self.handler = AppDeploymentHandler()

    def cleanup(self):
        pass

    @context_from_args
    def initialize(self, context):
        pass

    @context_from_args
    def Deploy(self, context, Name=None):
        """ Deploys a TeraVM entity - a controller or a test module

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type Name: str
        """
        return self.handler.deploy(context, Name)


