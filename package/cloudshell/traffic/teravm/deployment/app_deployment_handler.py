import json
from uuid import uuid4

from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.api.cloudshell_api import InputNameValue


class AppDeploymentHandler:
    def __init__(self):
        pass

    def deploy(self, context, Name=None):
        """ Deploys a TeraVM entity - a controller or a test module

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type Name: str
        """
        api = get_cloudshell_session(context)
        api.ExecuteCommand(context.reservation.reservation_id,
                           context.resource.attributes['TVM MA Name'],
                           "Resource",
                           "deploy_tvm",
                           [InputNameValue(Name='request',
                                           Value='Lolwhut')]
                           )
        # use connectivity to get cs session
        # get connectors details
        # get resource details
        # get request details
        fake_app = {
            'vm_name': 'lolwhocarez',
            'vm_uuid': str(uuid4()),
            'cloud_provider_resource_name': context.resource.attributes['vCenter Name']
        }

        return json.dumps(fake_app)
