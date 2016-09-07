from collections import OrderedDict
from cloudshell.shell.core.dependency_injection.context_based_logger import get_logger_with_thread_id

DEFAULT_PROMPT = r':~\$'
PROMPT = r':~\$'

CONNECTION_TYPE = 'ssh'
DEFAULT_CONNECTION_TYPE = 'ssh'

GET_LOGGER_FUNCTION = get_logger_with_thread_id
POOL_TIMEOUT = 300
ERROR_MAP = OrderedDict({r'Could not check out the required': 'Failed to acquire teravm license',
                         r'command not found': 'command not found',
                         r'NullPointerException': 'NullPointerException',
                         r'DiversifEyeException': 'DiversifEyeException'})

EXIT_CONFIG_MODE_PROMPT_COMMAND = ENTER_CONFIG_MODE_PROMPT_COMMAND = lambda *args, **kwargs: ''
COMMAND_RETRIES = 1