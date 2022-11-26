# Copyright (c) 2022 Olivier Clavel <olivier.clavel@thoteam.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: var_as_file
    author:
      - Olivier Clavel (@zeitounator)
    requirements:
      - 'For automatic temporary file cleanup: activate the clean_var_as_file callback'
    short_description: Get a file path containing a variable/content
    description:
      - Creates a temporary file with the content passed as argument
        and returns its path on the controller.
    options:
      _content:
        description: the content that should be included in the file.
        required: True
    notes:
      - 'Known issue: does not (yet) support concurrency from different process/users.'
      - 'This lookup will create the files in /tmp with read/write rights for the current user on the controller.'
      - 'If creating a file for the first time, it will initiate a var_as_file_index.txt containing the names of
        the created files during a run. This file will later be read by the clean_var_as_file callback to remove
        those files.'
'''

EXAMPLES = """
- name: Get a filename with the given content for later use
  ansible.builtin.set_fact:
    my_tmp_file: "{{ lookup('thoteam.var_as_file.var_as_file', some_variable) }}"

- name: Use in place in a module where a file is mandatory and you have the content in a var
  community.general.java_cert:
    pkcs12_path: "{{ lookup('thoteam.var_as_file.var_as_file', pkcs12_store_from_vault) }}"
    cert_alias: default
    keystore_path: /path/to/my/keystore.jks
    keystore_pass: changeit
    keystore_create: yes
    state: present
"""

RETURN = """
  _raw:
    description:
      - path to the temporary file with the content.
    type: str
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.thoteam.var_as_file.plugins.module_utils.var_as_file import VAR_AS_FILE_TRACK_FILE
from hashlib import sha256
import tempfile
import json
import os


def _hash_content(content):
    """
    Returns the hex digest of the sha256 sum of content
    """
    return sha256(content.encode()).hexdigest()


class LookupModule(LookupBase):

    created_files = dict()

    def _load_created(self):
        if os.path.exists(VAR_AS_FILE_TRACK_FILE):
            with open(VAR_AS_FILE_TRACK_FILE, 'r') as jfp:
                self.created_files = json.load(jfp)

    def _store_created(self):
        """
        serialize the created files as json in tracking file
        """

        with open(VAR_AS_FILE_TRACK_FILE, 'w') as jfp:
            json.dump(self.created_files, jfp)

    def run(self, terms, variables=None, **kwargs):

        '''
        terms contains the content to be written to the temporary file
        '''
        try:
            self._load_created()

            ret = []
            for content in terms:
                content_sig = _hash_content(content)
                file_exists = False

                # Check if file was already create for this content and check it.
                if content_sig in self.created_files:
                    if os.path.exists(self.created_files[content_sig]):
                        with open(self.created_files[content_sig], 'r') as efh:
                            if content_sig == _hash_content(efh.read()):
                                file_exists = True
                                ret.append(self.created_files[content_sig])
                            else:
                                os.remove(self.created_files[content_sig])

                # Create / Replace the file
                if not file_exists:
                    temp_handle, temp_path = tempfile.mkstemp(text=True)
                    with os.fdopen(temp_handle, 'a') as temp_file:
                        temp_file.write(content)
                        self.created_files[content_sig] = temp_path
                        ret.append(temp_path)

            self._store_created()

            return ret

        except Exception as e:
            raise AnsibleError(to_native(repr(e)))
