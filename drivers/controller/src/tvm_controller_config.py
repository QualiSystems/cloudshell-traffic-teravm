from collections import OrderedDict
import re
from cloudshell.shell.core.context_utils import get_decrypted_password_by_attribute_name_wrapper, \
    get_attribute_by_name_wrapper
from cloudshell.shell.core.dependency_injection.context_based_logger import get_logger_with_thread_id

DEFAULT_PROMPT = r'[#>\$]\s*$'
PROMPT = r'[#>\$]\s*$'

CONNECTION_TYPE = 'ssh'
DEFAULT_CONNECTION_TYPE = 'ssh'

GET_LOGGER_FUNCTION = get_logger_with_thread_id
POOL_TIMEOUT = 300
ERROR_MAP = OrderedDict({r'.*command not found': 'command not found', r'.*NullPointerException': 'NullPointerException',
                         r'.*DiversifEyeException': 'DiversifEyeException'})
