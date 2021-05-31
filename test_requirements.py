import pytest
from collections import defaultdict
from pprint import pprint


from requirement_resolver import add_entries, get_pending_requirements
from util import list_plugins


def test_requirements():
    add_entries(list_plugins())
    pending_requirements = defaultdict(list)
    for p in list_plugins():
        pending_requirements = get_pending_requirements(p.name, mutable_result=pending_requirements)

    pprint(pending_requirements, indent=3)
