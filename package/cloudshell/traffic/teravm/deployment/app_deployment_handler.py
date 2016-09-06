import json

from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.traffic.teravm.models.tvm_request import TvmAppRequest
from cloudshell.traffic.teravm.common.parsing_utilities import lowercase_and_underscores
from cloudshell.traffic.teravm.common import i18n as c


class AppDeploymentHandler:
    def __init__(self):
        pass

    @staticmethod
    def deploy(context, Name=None):
        """ Deploys a TeraVM entity - a controller or a test module

        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type Name: str
        """
        api = get_cloudshell_session(context)
        app_request = TvmAppRequest.from_context(context, api)
        deploy_result = api.ExecuteCommand(context.reservation.reservation_id,
                                           context.resource.attributes['TVM MA Name'],
                                           "Resource",
                                           "deploy_tvm",
                                           [InputNameValue(Name='request',
                                                           Value=app_request.to_string())])

        deployed_vm = json.loads(deploy_result.Output)

        app = {
            'vm_name': deployed_vm['vm_name'],
            'vm_uuid': deployed_vm['vm_uuid'],
            'cloud_provider_resource_name': context.resource.attributes.pop('vCenter Name', None),
        }

        # {'Refresh IP Timeout': '600', 'Auto Power On': 'False', 'Auto Delete': 'False', 'Wait for IP': 'False',
        #  'Auto Power Off': 'False', 'Auto Refresh IP': 'False', 'TVM MA Name': 'tvmma', 'tvm_license_server'}
        app.update(lowercase_and_underscores(context.resource.attributes))

        app[c.KEY_INDEX_POOL] = '{0}_{1}_{2}'.format(app['cloud_provider_resource_name'], app['tvm_ma_name'],
                                                     app_request.model)
        return json.dumps(app)
