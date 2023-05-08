#!/usr/bin/env python
# pylint: ver3

import json
import requests

from ansible.errors import AnsibleFilterError

def make_request(method, session, allow_404=False, **kwargs):
    """ call out to AWX api and return json output

    Args:
        method (str): HTTP method to use with Requests
        session (requests.Session): Requests Session object created with proper auth and headers
        allow_404 (boolean): Allow 404 from endpoint. False will raise execption is 404
                             is recieved.
        **kwargs: Arbitrary keyword arguments.

    Keyword Args:
        url (str): URL to target
        params (dict optional): parameters to be used for url encoding
        data (dict optional): json formatted data

    Returns:
        Response (obj): Requests response object
        data (dict): json dictionary of Requests response
    """
    method = method.lower()
    avail_methods = ['get', 'post', 'put', 'patch', 'delete']
    return_data = {}
    if method not in avail_methods:
        raise Exception(f"Invalid method passed: '{method}'. Must be one of {avail_methods}")
    try:
        response = getattr(session, method)(url=kwargs.get('url'),
                                            params=kwargs.get('params', None),
                                            json=kwargs.get('data', None),
                                            verify=False)
        response.raise_for_status()
        try:
            return_data = response.json()
        except ValueError:
            pass
    except requests.exceptions.HTTPError as err:
        if allow_404 and response.status_code == 404:
            return_data = {}
        else:
            err_content = json.loads(err.response.content)
            err_msg = {"url": kwargs.get('url'),
                       "error": err_content}
            raise Exception(f"Error making a call to AWX: {err_msg}")
    return response, return_data


def ost_projects(projects, field, **kwargs):
    '''Parse project list response, return ids or names
       Params:
          projects: (required) OST response of all project objects
          field: (required) name|id
          purge: (optional) purge all projects true/false
    '''
    fields = ['name', 'id']
    if field.lower() not in fields:
        raise AnsibleFilterError(f'Field: {field} is unacceptable. {fields}')
    env = kwargs.get('env', None)
    purge = kwargs.get('purge', None)
    my_return = []
    project_list = json.loads(projects['content']).get('projects', None)
    if not isinstance(project_list, list):
        raise AnsibleFilterError('project_list is required to be a dictionary')

    if env and purge in [ 'false', 'False', False, None ]:
        found_item = next(( item[field] for item in project_list \
                            if kwargs['env'] in item['name'] and \
                            'admin' not in item['name']), None)
        if found_item:
            my_return.append(found_item)

    # Return all satellite id/name
    if purge in [ 'true', 'True', True ]:
        all_envs = []
        for ost_project in project_list:
            if ost_project['name'] == env_name:
                core = ost_project[field]
            try:
                all_envs.append(next (( ost_project[field] for hp_sat in kwargs['all_envs'] \
                            if f"{env_name}{all_envs['envname']}" == ost_project['name'] or \
                            env_name in ost_project['name'])))
            except StopIteration:
                continue

        if core:
            all_sats.remove(core)

        my_return = all_envs

    return my_return

def ost_secgroups(ost_prj_id_lst, ost_url, ost_token):
    '''Parse project list response, return ids or names
       Params:
          ost_prj_id_list: (required) List of OST security groups
          ost_url: (required) Openstack URL
          ost_token: (required) Openstack auth token
    '''

    ost_session = requests.Session()
    ost_session.headers.update({'X-Auth-Token': ost_token})

    sec_groups_return = []
    if not isinstance(ost_prj_id_lst, list):
        raise AnsibleFilterError('ost_prj_id_lst is required to be a list')

    for prj_id in ost_prj_id_lst:
        security_groups = make_request(method='get',
                                       session=ost_session,
                                       url=f"{ost_url}:9696/v2.0/security-groups",
                                       params={"project_id": prj_id})

        for sec_group in security_groups[1]['security_groups']:
            sec_groups_return.append(sec_group['id'])


    return sec_groups_return



class FilterModule():
    '''Ansible filter module declaration'''

    def filters(self):
        '''Override filters method'''
        return {
            'ost_projects': ost_projects,
            'ost_secgroups': ost_secgroups
        }

