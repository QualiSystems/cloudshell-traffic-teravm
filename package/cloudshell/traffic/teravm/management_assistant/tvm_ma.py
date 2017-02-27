import json
import re
import uuid
from pyVim.connect import SmartConnect, Disconnect

from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.traffic.teravm.management_assistant.tvmma_controller import TVMManagerController
from cloudshell.traffic.teravm.models.deployment_configuration import DeploymentConfiguration
from cloudshell.traffic.teravm.models.tvm_request import TvmAppRequest
from cloudshell.traffic.teravm.models.tvm_ma_model import TVMMAModel
import cloudshell.traffic.teravm.common.error_messages as e
from cloudshell.traffic.teravm.common.path_utilties import combine_path
from cloudshell.traffic.teravm.common.cloudshell_helper import get_cloudshell_session
from cloudshell.traffic.teravm.common import i18n as c


class TeraVMManagementAssistantDriverHandler:
    def __init__(self):
        pass

    @staticmethod
    def deploy_tvm(context, request):
        app_request = TvmAppRequest.from_dict(json.loads(request))
        tvm_ma_model = TVMMAModel.from_context(context)

        api = get_cloudshell_session(context)

        pool_id = '{0}_{1}_{2}'.format(app_request.vcenter_address, context.resource.name, app_request.model)

        start_request = {
            'isolation': 'Exclusive',
            'reservationId': context.reservation.reservation_id,
            'poolId': pool_id,
            'ownerId': context.reservation.owner_user,
            'type': 'NextAvailableNumericFromRange',
            'requestedRange': {'Start': 3, 'End': 4000}
        }
        starting_index = api.CheckoutFromPool(json.dumps(start_request)).Items[0]

        conf = DeploymentConfiguration(app_request, tvm_ma_model, starting_index).to_dict()

        ma = TVMManagerController(tvm_ma_model.host_address)
        deployment_file_path = '/tmp/{0}'.format(uuid.uuid4())
        ma.set_configuration(conf, deployment_file_path)
        deploy_output = ma.deploy(deployment_file_path)

        try:
            if 'vim.fault.NoPermission' in deploy_output:
                raise Exception('Could not deploy VM, vCenter permission fault')
            deployed_vm_name = re.findall('Calling Object: (.*) Action: PowerOnVM', deploy_output)[0]
        except IndexError:
            raise Exception(e.DEPLOYMENT_FAILED + deploy_output)

        vsphere = pyVmomiService(SmartConnect, Disconnect, task_waiter=None)
        si = vsphere.connect(address=app_request.vcenter_address,
                             user=app_request.vcenter_user,
                             password=app_request.vcenter_password)

        vm = vsphere.find_vm_by_name(si, app_request.vcenter_default_datacenter, deployed_vm_name)

        app = json.dumps({
            'vm_name': deployed_vm_name + '_' + vm.config.uuid[-8:],
            'vm_uuid': vm.config.uuid,
            c.KEY_STARTING_INDEX: starting_index,
            c.KEY_INDEX_POOL: pool_id
        })

        if tvm_ma_model.vm_location != '':
            folder_path = combine_path(app_request.vcenter_default_datacenter, tvm_ma_model.vm_location)
            folder = vsphere.get_folder(si, folder_path)
            if folder is None:
                raise Exception('Could not find folder at ' + folder_path)
            folder.MoveInto([vm])

        return app
