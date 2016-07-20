from debug_utils import debugger
import json

from cloudshell.traffic.teravm.management_assistant.tvmma_controller import TVMManagerController
from cloudshell.traffic.teravm.models.deployment_configuration import DeploymentConfiguration
from cloudshell.traffic.teravm.models.tvm_request import TvmAppRequest
from cloudshell.traffic.teravm.models.tvm_ma_model import TVMMAModel


class TeraVMManagementAssistantDriverHandler:
    def __init__(self):
        pass

    @staticmethod
    def deploy_tvm(context, request):
        debugger.attach_debugger()

        tvm_app_request = TvmAppRequest.from_dict(json.loads(request))
        tvm_ma_model = TVMMAModel.from_context(context)
        conf = DeploymentConfiguration(tvm_app_request, tvm_ma_model).to_dict()

        mac = TVMManagerController(tvm_ma_model.host_address)
        mac.set_configuration(conf)
        deploy_output = mac.deploy()
        print deploy_output
        # get vm name
        # grab vm uuid (need vmware sdk for this)
        return 'lolz'  # return str json of vm uuid & vm name
