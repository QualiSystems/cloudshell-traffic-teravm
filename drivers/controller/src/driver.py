from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context_utils import context_from_args
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
from cloudshell.traffic.teravm.controller.driver_handler import TVMControllerHandler
from tvm_cli_service import TvmCliService

import tvm_controller_config


class TeraVMController:
    def __init__(self):
        bootstrap = DriverBootstrap()
        bootstrap.initialize()
        bootstrap.add_config(tvm_controller_config)
        cli_service = TvmCliService()
        self.handler = TVMControllerHandler(cli_service)

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    @context_from_args
    def load_configuration(self, context, test_location):
        return self.handler.load_configuration(context, test_location)

    @context_from_args
    def preview_configuration(self, context, test_location):
        return self.handler.preview_configuration(context, test_location)

    @context_from_args
    def run_test(self, context):
        return self.handler.run_test(context)

    @context_from_args
    def stop_test(self, context):
        return self.handler.stop_test(context)

    @context_from_args
    def get_inventory(self, context):
        return self.handler.get_inventory(context)

    @context_from_args
    def run_custom_command(self, context, command_text):
        return self.handler.run_custom_command(context, command_text)

