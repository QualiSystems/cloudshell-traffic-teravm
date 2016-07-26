import json

from cloudshell.traffic.teravm.common import i18n, error_messages


class DeploymentConfiguration:
    """ the configuration of tvm deployment command as tvmma understands it """
    def __init__(self, tvm_app_request, tvm_ma_details):
        """
        :type tvm_app_request: cloudshell.traffic.teravm.models.tvm_request.TvmAppRequest
        :type tvm_ma_details: cloudshell.traffic.teravm.models.tvm_ma_model.TVMMAModel
        :return:
        """

        self._config = {}

        self._tvmma = tvm_ma_details
        self._request = tvm_app_request

        if self._request.model == i18n.CONTROLLER_MODEL:
            self._build_controller_config()

        elif self._request.model == i18n.TEST_MODULE_MODEL:
            self._build_test_module_config()

        else:
            raise Exception(error_messages.UNSUPPORTED_MODEL)

    def _build_controller_config(self):
        self._config = {
            'vmuTypes': 'TVM-C',
            'vmcCount': 1,
            'vmcServer': self._request.vcenter_address,
            'vmcUser': self._request.vcenter_user,
            'vmcPassword': self._request.vcenter_password,
            'vmcHost[0]': self._tvmma.esxi_host,
            'vmcDatastore[0]': self._tvmma.datastore,
            'vmcNetsByNic[0]': self._tvmma.comms_network,
            'vmcNetsByNic[1]': self._tvmma.management_network,
            'vmcOva': './ova/'
        }

    def _build_test_module_config(self):
        self._config = {
            'vmuTypes': self._request.tvm_type,
            'tvmCount': 1,
            'tvmServer': self._request.vcenter_address,
            'tvmUser': self._request.vcenter_user,
            'tvmPassword': self._request.vcenter_password,
            'tvmHost[0]': self._tvmma.esxi_host,
            'tvmDatastore[0]': self._tvmma.datastore,
            'tvmNetsByNic[0]': self._tvmma.comms_network,
            'tvmNetsByNic[1]': self._tvmma.management_network,
            'tvmOva': './ova/'
        }
        for index in range(self._request.number_of_interfaces):
                self._config["tvmNetsByNic[%s]" % str(index+1)] = self._tvmma.holding_network

    def __str__(self):
        return json.dumps(self._config)

    def to_jsonstring(self):
        return self.__str__()

    def to_dict(self):
        return self._config



