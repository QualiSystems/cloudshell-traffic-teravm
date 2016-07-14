import json

from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from uuid import uuid4


class TeraVMManagementAssistant(ResourceDriverInterface):
    def __init__(self):
        pass

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def deploy_tvm(self, context, request):

        fake_app = {
            'vm_name': 'lolwhocarez',
            'vm_uuid': str(uuid4()),
            'cloud_provider_resource_name': 'vcenter9'
        }

        return json.dumps(fake_app)

