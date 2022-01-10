# Ansible Collection - thoteam.var_as_file

<!--ts-->
* [Ansible Collection - thoteam.var_as_file](#ansible-collection---thoteamvar_as_file)
   * [DISCLAIMER](#disclaimer)
   * [Description](#description)
   * [Technical details](#technical-details)
      * [thoteam.var_as_file.var_as_file lookup plugin](#thoteamvar_as_filevar_as_file-lookup-plugin)
      * [thoteam.var_as_file.clean_var_as_file callback plugin](#thoteamvar_as_fileclean_var_as_file-callback-plugin)
      * [Security](#security)
   * [Installing the collection](#installing-the-collection)
   * [Configuring ansible to run the callback](#configuring-ansible-to-run-the-callback)
   * [Testing with the collection test playbook](#testing-with-the-collection-test-playbook)
   * [Using the lookup in your own playbook](#using-the-lookup-in-your-own-playbook)
   * [Licence and copyright](#licence-and-copyright)
<!--te-->

## DISCLAIMER
**This is an ongoing and alpha stage work. It has not yet been tested in a lot of situation and might suffer from bugs
making it unusable with some modules. More over (see [Security](#security) below), it is not compatible with ansible
concurrent use yet and some data currently persisted on disk should be stored elsewhere. Use at your own risk**

## Description

This work was inspired by [a question asked on StackOverflow][Initial SO question]. The goal was to
- provide a mechanism to automatically transform a variable to a file with its content
- return the file name so it can be used in any place a file is expected
- clean-up after running the playbook all files that were created

## Technical details
The collection contains 2 plugins 

### thoteam.var_as_file.var_as_file lookup plugin
* The lookup plugin receives the content and creates a temporary file with it using the python method `tempfile.mkstemp()`
* The content is sha256 hashed. This hash is used to reference the above file path in a dictionnary which is persisted
  on disk as json in a static file (currently `/tmp/var_as_file_track.json`).
* When a new content is asked as file, if it has already, the corresponding file exists and its content has the same hash,
  its path is returned. Else it is deleted prior to be recreated.

### thoteam.var_as_file.clean_var_as_file callback plugin
That one is responsible for cleaning up. It listens to the `v2_playbook_on_stats` callback event and
* deletes all files references in the json tracking file
* deletes the tracking file

### Security
Content files are created via `tempfile.mkstemp` and should be rather secure (accessible to user only,
created with a random name, cleared after playbook run)

There are still some concerns:
* Storing the file list a json static file is not ideal, although the content file should be secure this won't work
  in multiple user scenario (@todo: find a way to store that info in some ansible cache / stat / fact)
* We launch cleanup on `stats` phase. What happens if ansible crashes before?

## Installing the collection
```console
ansible-galaxy collection install git+https://github.com/ansible-ThoTeam/thoteam.var_as_file.git,main
```

## Configuring ansible to run the callback
Note:
* the lookup plugin will run without any problem without the callback enabled. But the temporary files will
remain on disk and the tracking files will be left intact. If you enable the callback at a later stage, it will clean-up
all the existing files it can find.
* although the callback should be enabled by default, it looks like it does not work for those bundled in a collection.
  so enabling is necessary.

To enable the callback, add it to the list of `callbacks_enabled` in `ansible.cfg`
```ini
callbacks_enabled=thoteam.var_as_file.clean_var_as_file
```
Note: if you had an other plugin up there, add all existing separated by a coma.

## Testing with the collection test playbook
1. First make sure the track file does not exist. If it does, delete it
    ```console
    $ ls /tmp/var_as_file_track.json
    ls: cannot access '/tmp/var_as_file_track.json': No such file or directory
    ```
2. Run the test playbook provided in the collection. It will only use the lookup plugin to use a var as file and
   show its content
    ```console
    ansible-playbook thoteam.var_as_file.test
    ```
3. Upon sucessful completion of the playbook, repeat step1 to make sure the tracking file was removed
   (and the corresponding temporary files)

## Using the lookup in your own playbook
You can use the lookup as a jinja2 template for any other variable or directly as an entry to a module parameter.

Here is an extract of the examples in the inline doc (auto-generated one day maybe....):
```yaml
- name: Get a filename with the given content for later use
  ansible.builtin.set_fact:
    my_tmp_file: "{{ lookup('thoteam.var_as_file.var_as_file', some_variable) }}
    
- name: Use in place in a module where a file is mandatory and you have the content in a var
  community.general.java_cert:
    pkcs12_path: "{{ lookup('thoteam.var_as_file.var_as_file', pkcs12_store_from_vault) }}"
    cert_alias: default
    keystore_path: /path/to/my/keystore.jks
    keystore_pass: changeit
    keystore_create: yes
    state: present
```

## Licence and copyright
GNU GENERAL PUBLIC LICENSE v3 or later</br>
(c) 2022 Olivier Clavel <olivier.clavel@thoteam.com></br>
See [COPYING](COPYING) or https://www.gnu.org/licenses/gpl-3.0.en.html


[Initial SO question]: https://stackoverflow.com/questions/70624954