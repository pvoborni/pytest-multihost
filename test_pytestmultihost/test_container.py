#
# Copyright (C) 2020 pytest-multihost contributors. See COPYING for license
#

import getpass
import pytest
from subprocess import CalledProcessError
import contextlib
import sys
import os
import subprocess

import pytest_multihost
import pytest_multihost.transport
from pytest_multihost.config import Config


def get_conf_dict(id1, id2):
    return {
        'transport': 'podman',
        'ssh_username': getpass.getuser(),
        'domains': [
            {
                'name': 'localdomain',
                'hosts': [
                    {
                        'name': 'container1',
                        'external_hostname': 'container1',
                        'ip': '192.168.155.155',
                        'host_id': id1,
                        'role': 'local',
                    },
                    {
                        'name': 'container2',
                        'external_hostname': 'container2',
                        'ip': '192.168.155.156',
                        'host_id': id2,
                        'username': '__nonexisting_test_username__',
                        'role': 'badusername',
                    },
                ],
            },
        ],
    }


@pytest.fixture(scope='class', params=['podman'])
def containers(request):
    cmd = ['podman', 'run', '-d', '-ti', 'fedora']
    res = subprocess.run(cmd, capture_output=True, text=True)
    res2 = subprocess.run(cmd, capture_output=True, text=True)
    container1_id = res.stdout.strip()
    container2_id = res2.stdout.strip()
    ids = [container1_id, container2_id]

    yield ids

    for cont_id in ids:
        cmd = ['podman', 'stop', cont_id]
        subprocess.run(cmd)


@pytest.fixture(scope='class')
def multihost(request, containers):
    conf = get_conf_dict(containers[0], containers[1])
    mh = pytest_multihost.make_multihost_fixture(
        request,
        descriptions=[
            {
                'hosts': {
                    'local': 1,
                },
            },
        ],
        _config=Config.from_dict(conf),
    )
    assert conf == get_conf_dict(containers[0], containers[1])
    mh.host = mh.config.domains[0].hosts[0]
    assert isinstance(mh.host.transport, pytest_multihost.transport.PodmanTransport)
    yield mh.install()


class TestContainer(object):
    def test_echo(self, multihost):
        host = multihost.host

        echo = host.run_command(['echo', 'hello', 'world'], raiseonerr=False)
        print(echo.stdout_text)
        print(echo.stderr_text)
        assert echo.stdout_text == 'hello world\n'
