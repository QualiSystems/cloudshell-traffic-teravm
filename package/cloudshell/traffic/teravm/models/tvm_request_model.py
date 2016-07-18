import json


class TVMRequest:
    def __init__(self, context, api):
        app = AppDetails(context, api)
        if app.model == 'TeraVM Controller':
            request = self._tvm_controller_request(app.attributes)
        elif app.model == 'TeraVM Test Module':
            request = self._tvm_test_module_request(app.attributes)
        else:
            Exception('Tried to deploy unexpected model ' + app.model)
        self.request = request

    def __str__(self):
        return json.dumps(self.request)

    def _tvm_controller_request(self, attributes):
        return self._basic_request(attributes)

    def _tvm_test_module_request(self, attributes):
        return self._basic_request(attributes)

    @staticmethod
    def _basic_request(attributes):
        request = {
            'vcenter_address': attributes['vcenter_address'],
            'vcenter_user': attributes['User'],
            'vcenter_password': attributes['Password'],
            'holding_network': attributes['Holding Network']
        }
        return request


class AppDetails:
    def __init__(self, context, api):
        """

        :type context: todo
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        deployment = context.resource
        self._attributes = self._get_vcenter_attributes(api, deployment)
        self._attributes.update(deployment.attributes)
        self._app = json.loads(deployment.app_context.app_request_json)

    @staticmethod
    def _get_vcenter_attributes(api, deployment):
        vcenter_name = deployment.attributes['vCenter Name']
        res = api.GetResourceDetails(vcenter_name)
        ra = res.ResourceAttributes
        result = {attribute.Name: attribute.Value for attribute in ra}
        result['vcenter_address'] = res.Address
        result['Password'] = api.DecryptPassword(result['Password']).Value
        return result

    @property
    def attributes(self):
        return self._attributes

    @property
    def model(self):
        return self._app['logicalResource']['model']
