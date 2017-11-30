import json

import jsonpickle

from cloudshell.traffic.teravm.common import i18n as c, error_messages


class TvmAppRequest:
    """ Gets attributes and other data about request from the deploying app """
    def __init__(self, vcenter_address, vcenter_user, vcenter_password, vcenter_default_datacenter, requested_model,
                 number_of_interfaces=2, tvm_type=None, ports_logical_names=''):

        self.vcenter_address = vcenter_address
        self.vcenter_user = vcenter_user
        self.vcenter_password = vcenter_password
        self.vcenter_default_datacenter = vcenter_default_datacenter
        self.model = requested_model
        self.number_of_interfaces = number_of_interfaces
        self.tvm_type = tvm_type
        self.ports_logical_names = ports_logical_names

    @classmethod
    def from_context(cls, context, api):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :rtype: TvmAppRequest
        """
        app = AppDetails(context, api)
        request = app.attributes
        request[c.KEY_MODEL] = app.model
        number_of_ports = int(request[c.ATTRIBUTE_NAME_NUMBER_OF_PORTS])
        request[c.ATTRIBUTE_NAME_NUMBER_OF_PORTS] = 2 if number_of_ports == 0 else number_of_ports
        num_of_conns = len(app.connections)
        if 0 < request[c.ATTRIBUTE_NAME_NUMBER_OF_PORTS] < num_of_conns:
            raise Exception('More connections configured to app than requested ports\n'
                            'You requested {0} connections and {1} ports'.format(num_of_conns, request[c.ATTRIBUTE_NAME_NUMBER_OF_PORTS]))
        return cls.from_dict(request)

    @classmethod
    def from_string(cls, jsonstr):
        """
        :type jsonstr: str
        :rtype: TvmAppRequest
        """
        request = json.loads(jsonstr)
        return cls.from_dict(request)

    @classmethod
    def from_dict(cls, request_dict):
        """
        :type request_dict: dict
        :rtype: TvmAppRequest
        """
        if c.ATTRIBUTE_NAME_TVM_TYPE not in request_dict:
            request_dict[c.ATTRIBUTE_NAME_TVM_TYPE] = c.DEFAULT_TVM_TYPE

        if c.ATTRIBUTE_PORTS_LOGICAL_NAMES not in request_dict:
            request_dict[c.ATTRIBUTE_PORTS_LOGICAL_NAMES] = c.DEFAULT_PORTS_LOGICAL_NAMES

        return cls(request_dict[c.KEY_VCENTER_ADDRESS],
                   request_dict[c.ATTRIBUTE_NAME_USER],
                   request_dict[c.ATTRIBUTE_NAME_PASSWORD],
                   request_dict[c.ATTRIBUTE_NAME_DEFAULT_DATACENTER],
                   request_dict[c.KEY_MODEL],
                   request_dict[c.ATTRIBUTE_NAME_NUMBER_OF_PORTS],
                   request_dict[c.ATTRIBUTE_NAME_TVM_TYPE],
                   request_dict[c.ATTRIBUTE_PORTS_LOGICAL_NAMES])

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
            c.ATTRIBUTE_NAME_NUMBER_OF_PORTS: self.number_of_interfaces,
            c.ATTRIBUTE_NAME_TVM_TYPE: self.tvm_type,
            c.ATTRIBUTE_PORTS_LOGICAL_NAMES: self.ports_logical_names
        }


class AppDetails:
    def __init__(self, context, api):
        """
        :type context: cloudshell.shell.core.context.ResourceCommandContext
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        deployment = context.resource
        app_name = self._get_app_name(deployment)
        reservation_details = _get_reservation_details(api, context)
        self._connections = self._get_app_connections(reservation_details, app_name)
        self._attributes = self._get_vcenter_attributes(api, deployment)
        self._attributes.update(deployment.attributes)
        if c.ATTRIBUTE_NAME_NUMBER_OF_PORTS not in self._attributes.keys():
            self._attributes[c.ATTRIBUTE_NAME_NUMBER_OF_PORTS] = -1
        self._app = json.loads(deployment.app_context.app_request_json)

    @staticmethod
    def _get_app_name(deployment):
        return json.loads(deployment.app_context.app_request_json)['name']

    @staticmethod
    def get_vcenter_name(deployment):

        app_request = jsonpickle.decode(deployment.app_context.app_request_json)

        cloud_provider_name = app_request["deploymentService"].get("cloudProviderName")
        # Cloudshell >= v7.2 have no vCenter Name attribute, fill it from the cloudProviderName context attr
        if cloud_provider_name:
            vcenter_name = cloud_provider_name
        else:
            vcenter_name = deployment.attributes[c.ATTRIBUTE_NAME_VCENTER_NAME]
        return vcenter_name

    @staticmethod
    def _get_vcenter_attributes(api, deployment):
        vcenter_name = AppDetails.get_vcenter_name(deployment)
        res = api.GetResourceDetails(vcenter_name)
        ra = res.ResourceAttributes
        result = {attribute.Name: attribute.Value for attribute in ra}
        result[c.KEY_VCENTER_ADDRESS] = res.Address
        result[c.ATTRIBUTE_NAME_PASSWORD] = api.DecryptPassword(result[c.ATTRIBUTE_NAME_PASSWORD]).Value
        return result

    @staticmethod
    def _get_app_connections(reservation_details, app_name):
        """
        :type reservation_details: cloudshell.api.cloudshell_api.ReservationDescriptionInfo
        :type app_name: str
        :rtype: cloudshell.api.cloudshell_api.Connector
        """
        connections = reservation_details.Connectors
        return [conn for conn in connections if conn.Source == app_name or conn.Target == app_name]

    @property
    def attributes(self):
        return self._attributes

    @property
    def model(self):
        return self._app['logicalResource']['model']

    @property
    def connections(self):
        return self._connections


def _get_reservation_details(api, context):
    """
    :rtype: cloudshell.api.cloudshell_api.ReservationDescriptionInfo
    """
    resid = context.reservation.reservation_id
    return api.GetReservationDetails(resid).ReservationDescription
