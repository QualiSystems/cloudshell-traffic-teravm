from cloudshell.api.cloudshell_api import CloudShellAPISession

SESSION_CLASS = CloudShellAPISession


def get_cloudshell_session(context):
    return _get_cloudshell_session(server_address=context.connectivity.server_address,
                                   token=context.connectivity.admin_auth_token,
                                   reservation_domain=context.reservation.domain)


def _get_cloudshell_session(server_address, token, reservation_domain):
    return SESSION_CLASS(host=server_address,
                         token_id=token,
                         username=None,
                         password=None,
                         domain=reservation_domain)
