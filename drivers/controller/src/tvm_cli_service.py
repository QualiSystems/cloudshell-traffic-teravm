import inject
from cloudshell.configuration.cloudshell_cli_binding_keys import SESSION
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER
from cloudshell.cli.service.cli_service import CliService
from scp import SCPClient


class TvmCliService(CliService):

    @inject.params(session=SESSION, logger=LOGGER)
    def send_file(self, local_path, remote_path, session=None, logger=None):
        if not session:
            session.connect()
        scp = SCPClient(session._handler.get_transport())
        scp.put(local_path, remote_path)

    def rollback(self, expected_map=None):
        pass
