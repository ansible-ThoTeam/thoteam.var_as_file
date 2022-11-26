# Copyright (c) 2022 Olivier Clavel <olivier.clavel@thoteam.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
name: clean_var_as_file
type: utility
short_description: Cleans-up files created by the var_as_file lookup
description:
    - This callback will clean-up all files created by the var_as_file lookup during the play
author:
    - Olivier Clavel (@zeitounator)
requirements:
    - None at this stage
options: []
notes: []
'''

from ansible.plugins.callback import CallbackBase
from ansible_collections.thoteam.var_as_file.plugins.module_utils.var_as_file import VAR_AS_FILE_TRACK_FILE
from ansible.module_utils.common.text.converters import to_native
from ansible.errors import AnsibleError
import os
import json

def _make_clean():
    """Clean all files listed in VAR_AS_FILE_TRACK_FILE"""
    try:
        if (os.path.exists(VAR_AS_FILE_TRACK_FILE)):
            with open(VAR_AS_FILE_TRACK_FILE, 'r') as jfp:
                files = json.load(jfp)
                for f in files.values():
                    os.remove(f)
            os.remove(VAR_AS_FILE_TRACK_FILE)
    except Exception as e:
        raise AnsibleError(to_native(repr(e)))

class CallbackModule(CallbackBase):
    ''' This Ansible callback plugin cleans-up files created by the thoteam.var_as_file.var_as_file lookup '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'utility'
    CALLBACK_NAME = 'thoteam.var_as_file.clean_var_as_file'

    CALLBACK_NEEDS_WHITELIST = False
    # This one doesn't work for a collection plugin
    # Needs to be enabled anyway in ansible.cfg callbacks_enabled option
    CALLBACK_NEEDS_ENABLED = False

    def v2_playbook_on_stats(self, stats):
        _make_clean()
