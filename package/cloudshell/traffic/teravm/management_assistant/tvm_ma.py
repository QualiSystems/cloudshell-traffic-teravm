from debug_utils import debugger
import json
import re

from cloudshell.traffic.teravm.management_assistant.tvmma_controller import TVMManagerController
from cloudshell.traffic.teravm.models.deployment_configuration import DeploymentConfiguration
from cloudshell.traffic.teravm.models.tvm_request import TvmAppRequest
from cloudshell.traffic.teravm.models.tvm_ma_model import TVMMAModel
import cloudshell.traffic.teravm.common.error_messages as e

from cloudshell.traffic.teravm.common.vmware.vsphere import VSphere
from pyVmomi import vim


class TeraVMManagementAssistantDriverHandler:
    def __init__(self):
        pass

    @staticmethod
    def deploy_tvm(context, request):
        debugger.attach_debugger()

        deployed = {}

        app_request = TvmAppRequest.from_dict(json.loads(request))
        tvm_ma_model = TVMMAModel.from_context(context)
        conf = DeploymentConfiguration(app_request, tvm_ma_model).to_dict()

        mac = TVMManagerController(tvm_ma_model.host_address)
        mac.set_configuration(conf)
        deploy_output = mac.deploy()

        try:
            deployed_vm_name = re.findall('Calling Object: (.*) Action: PowerOnVM', deploy_output)[0]
        except IndexError:
            raise Exception(e.DEPLOYMENT_FAILED + deploy_output)
        vsphere = VSphere(address=app_request.vcenter_address,
                          user=app_request.vcenter_user,
                          password=app_request.vcenter_password)
        vm = vsphere.try_get_obj([vim.VirtualMachine], deployed_vm_name)
        # move vm to target location (maybe take location from vcenter?) (is it tvmma responsibility????)
        app = json.dumps({
            'vm_name': deployed_vm_name,
            'vm_uuid': vm.config.instanceUuid
        })
        return app
