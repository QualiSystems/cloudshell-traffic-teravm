import json

from cloudshell.traffic.teravm.common import i18n as c, error_messages


class TvmAppRequest:
    """ Gets attributes and other data about request from the deploying app """
    def __init__(self, vcenter_address, vcenter_user, vcenter_password, vcenter_default_datacenter, requested_model,
                 number_of_interfaces=2, tvm_type=None):

        self.vcenter_address = vcenter_address
        self.vcenter_user = vcenter_user
        self.vcenter_password = vcenter_password
        self.vcenter_default_datacenter = vcenter_default_datacenter
        self.model = requested_model
        self.number_of_interfaces = number_of_interfaces
        self.tvm_type = tvm_type

    @classmethod
    def from_context(cls, context, api):
        app = AppDetails(context, api)
        request = app.attributes
        request[c.KEY_MODEL] = app.model
        return cls.from_dict(request)

    @classmethod
    def from_string(cls, jsonstr):
        request = json.loads(jsonstr)
        return cls.from_dict(request)

    @classmethod
    def from_dict(cls, request_dict):
        if c.KEY_NUMBER_OF_INTERFACES not in request_dict:
            request_dict[c.KEY_NUMBER_OF_INTERFACES] = 2
        if c.ATTRIBUTE_NAME_TVM_TYPE not in request_dict:
            request_dict[c.ATTRIBUTE_NAME_TVM_TYPE] = c.DEFAULT_TVM_TYPE
        return cls(request_dict[c.KEY_VCENTER_ADDRESS],
                   request_dict[c.ATTRIBUTE_NAME_USER],
                   request_dict[c.ATTRIBUTE_NAME_PASSWORD],
                   request_dict[c.ATTRIBUTE_NAME_DEFAULT_DATACENTER],
                   request_dict[c.KEY_MODEL],
                   request_dict[c.KEY_NUMBER_OF_INTERFACES],
                   request_dict[c.ATTRIBUTE_NAME_TVM_TYPE])

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_string(self):
        return self.__str__()

    def to_dict(self):
        return {
            c.KEY_VCENTER_ADDRESS: self.vcenter_address,
            c.ATTRIBUTE_NAME_USER: self.vcenter_user,
            c.ATTRIBUTE_NAME_PASSWORD: self.vcenter_password,
            c.ATTRIBUTE_NAME_DEFAULT_DATACENTER: self.vcenter_default_datacenter,
            c.KEY_MODEL: self.model,
            c.KEY_NUMBER_OF_INTERFACES: self.number_of_interfaces,
            c.ATTRIBUTE_NAME_TVM_TYPE: self.tvm_type
        }


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
        vcenter_name = deployment.attributes[c.ATTRIBUTE_NAME_VCENTER_NAME]
        res = api.GetResourceDetails(vcenter_name)
        ra = res.ResourceAttributes
        result = {attribute.Name: attribute.Value for attribute in ra}
        result[c.KEY_VCENTER_ADDRESS] = res.Address
        result[c.ATTRIBUTE_NAME_PASSWORD] = api.DecryptPassword(result[c.ATTRIBUTE_NAME_PASSWORD]).Value
        return result

    @property
    def attributes(self):
        return self._attributes

    @property
    def model(self):
        return self._app['logicalResource']['model']
