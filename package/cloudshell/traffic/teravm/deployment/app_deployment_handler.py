import json
import inject
from uuid import uuid4

from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.traffic.teravm.models.tvm_request import TvmAppRequest


class AppDeploymentHandler:
    def __init__(self):
        pass

    def deploy(self, context, Name=None):
        """ Deploys a TeraVM entity - a controller or a test module

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type Name: str
        """
        api = get_cloudshell_session(context)
        # get connectors details
        request = TvmAppRequest.from_context(context, api).to_string()
        deploy_tvm_output = api.ExecuteCommand(context.reservation.reservation_id,
                                               context.resource.attributes['TVM MA Name'],
                                               "Resource",
                                               "deploy_tvm",
                                               [InputNameValue(Name='request',
                                                               Value=request)])

        # deploy_result = json.loads(deploy_tvm_output)
        # deploy_result.vm_name, deploy_result.vm_uuid
        fake_app = {
            'vm_name': 'lolwhocarez',
            'vm_uuid': str(uuid4()),
            'cloud_provider_resource_name': context.resource.attributes['vCenter Name']
        }

        return json.dumps(fake_app)

