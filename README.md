# fruit_facts

An Ansible playbook whose purpose is to demonstrate both Ansible and REST API concepts.

1. GETs all fruit data from [fruityvice.com](https://fruityvice.com)
2. Filter the dataset using a custom Ansible filter plugin
   * Filter based on Family and Genus
   * Returns a simplified dataset, including only Name and ID
3. Loop over filtered list, performing the following actions:
   * GET fruit object by ID
   * Create new dictionary with a subnet of data for each fruit in the filtered list from step 2.

  
---

```
Default: SSL Verification enabled
ansible-playbook -vv fruity_facts.yml

To disable SSL Verification:
ansible-playbook -vv fruity_facts.yml -e verify_ssl=false
```
