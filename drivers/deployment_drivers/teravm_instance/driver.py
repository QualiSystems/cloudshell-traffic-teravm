import json
from debug_utils import debugger

from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from uuid import uuid4


class DeployTeraVM(ResourceDriverInterface):
    def __init__(self):
        pass

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def Deploy(self, context, Name=None):
        debugger.attach_debugger()
        fake_app = {
            'vm_name': 'lolwhocarez',
            'vm_uuid': str(uuid4()),
            'cloud_provider_resource_name': 'vcenter9'
        }

        return json.dumps(fake_app)

