import json
from debug_utils import debugger

from uuid import uuid4
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session


class AppDeploymentHandler:
    def __init__(self):
        pass

    def deploy(self, context, Name=None):
        """ Deploys a TeraVM entity - a controller or a test module

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type Name: str
        """
        debugger.attach_debugger()
        api = get_cloudshell_session(context)
        api.ExecuteCommand(context.reservation.reservation_id,
                           context.resource.attributes['TVM MA Name'],
                           "Resource",
                           "deploy_tvm",
                           )
        # use connectivity to get cs session
        # get connectors details
        # get resource details
        # get request details
        fake_app = {
            'vm_name': 'lolwhocarez',
            'vm_uuid': str(uuid4()),
            'cloud_provider_resource_name': 'vcenter9'
        }

        return json.dumps(fake_app)
