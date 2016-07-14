from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface


class TeraVMController(ResourceDriverInterface):
    def __init__(self):
        pass

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def run_test(self, context, test_name):
        return 'Dummy executing test_name ' + test_name

    def stop_test(self, context):
        return 'Dummy stopping tests'

