import json
import re
from pyVim.connect import SmartConnect, Disconnect

from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.management_assistant.tvmma_controller import TVMManagerController
from cloudshell.traffic.teravm.models.deployment_configuration import DeploymentConfiguration
from cloudshell.traffic.teravm.models.tvm_request import TvmAppRequest
from cloudshell.traffic.teravm.models.tvm_ma_model import TVMMAModel
import cloudshell.traffic.teravm.common.error_messages as e
from cloudshell.traffic.teravm.common.path_utilties import combine_path


class TeraVMManagementAssistantDriverHandler:
    def __init__(self):
        pass

    @staticmethod
    def deploy_tvm(context, request):
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

        vsphere = pyVmomiService(SmartConnect, Disconnect, task_waiter=None)
        si = vsphere.connect(address=app_request.vcenter_address,
                             user=app_request.vcenter_user,
                             password=app_request.vcenter_password)

        vm = vsphere.find_vm_by_name(si, app_request.vcenter_default_datacenter, deployed_vm_name)

        app = json.dumps({
            'vm_name': deployed_vm_name,
            'vm_uuid': vm.config.uuid
        })

        if tvm_ma_model.vm_location != '':
            folder_path = combine_path(app_request.vcenter_default_datacenter, tvm_ma_model.vm_location)
            folder = vsphere.get_folder(si, folder_path)
            if folder is None:
                raise Exception('Could not find folder at ' + folder_path)
            folder.MoveInto([vm])

        return app
