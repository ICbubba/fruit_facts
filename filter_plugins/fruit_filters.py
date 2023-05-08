#!/usr/bin/env python

''' Python Ansible Filter to return simplified list of all fruits and their IDs '''

from ansible.errors import AnsibleFilterError



def fruit_filter(fruit_list, family=None, genus=None):
    '''Parse monitor list response, return name
       Params:
          family: (optional) e.g. Rosaceae
          genus: (optional) e.g. Fragaria
    '''

    filtered_list = []


    # Input data validation
    if not isinstance(fruit_list, list):
        raise AnsibleFilterError(f'fruit_list is required to be a list, got {type(fruit_list)}')


    # by family
    if isinstance(family, str) and genus is None:
        filtered_list = [ fruit for fruit in fruit_list
                          if family.lower() == fruit['family'].lower() ]

    # by genus
    elif isinstance(genus, str) and family is None:
        filtered_list = [ fruit for fruit in fruit_list
                          if genus.lower() == fruit['genus'].lower() ]

    # both family and genus
    elif all([isinstance(family, str), isinstance(genus, str)]):
        filtered_list = [ fruit for fruit in fruit_list
                          if family.lower() == fruit['family'].lower() and
                          genus.lower() == fruit['genus'].lower() ]

    # return fruit name and id only
    new_list = [ { 'name': fruit['name'], 'id': fruit['id'] } for fruit in filtered_list ]

    return new_list



class FilterModule():
    '''Ansible filter module declaration'''

    def filters(self):
        '''Override filters method'''
        return {
            'fruit_filter': fruit_filter
        }
