from cloudshell.api.cloudshell_api import CloudShellAPISession

SESSION_CLASS = CloudShellAPISession


def get_cloudshell_session(context, domain=None):

    if domain is None:
        domain = context.reservation.domain

    return _get_cloudshell_session(server_address=context.connectivity.server_address,
                                   token=context.connectivity.admin_auth_token,
                                   reservation_domain=domain)


def _get_cloudshell_session(server_address, token, reservation_domain):
    return SESSION_CLASS(host=server_address,
                         token_id=token,
                         username=None,
                         password=None,
                         domain=reservation_domain)


def get_attribute_value(attribute_name, resource):
    """
    :type attribute_name: str
    :type resource: cloudshell.api.cloudshell_api.ResourceInfo
    :return:
    """
    try:
        return (att.Value for att in resource.ResourceAttributes if att.Name == attribute_name).next()
    except StopIteration:
        raise Exception('No attribute named {0} on resource {1}'.format(attribute_name, resource.Name))
