"""ACME plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ....config import (
    IntegrationConfig,
)

from ....containers import (
    run_support_container,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class ACMEProvider(CloudProvider):
    """ACME plugin. Sets up cloud resources for tests."""
    DOCKER_SIMULATOR_NAME = 'acme-simulator'

    def __init__(self, args):  # type: (IntegrationConfig) -> None
        super(ACMEProvider, self).__init__(args)

        # The simulator must be pinned to a specific version to guarantee CI passes with the version used.
        if os.environ.get('ANSIBLE_ACME_CONTAINER'):
            self.image = os.environ.get('ANSIBLE_ACME_CONTAINER')
        else:
            self.image = 'quay.io/ansible/acme-test-container:2.0.0'

        self.uses_docker = True

    def setup(self):  # type: () -> None
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(ACMEProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def _setup_dynamic(self):  # type: () -> None
        """Create a ACME test container using docker."""
        ports = [
            5000,  # control port for flask app in container
            14000,  # Pebble ACME CA
        ]

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            self.DOCKER_SIMULATOR_NAME,
            ports,
            allow_existing=True,
            cleanup=True,
        )

        descriptor.register(self.args)

        self._set_cloud_config('acme_host', self.DOCKER_SIMULATOR_NAME)

    def _setup_static(self):  # type: () -> None
        raise NotImplementedError()


class ACMEEnvironment(CloudEnvironment):
    """ACME environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self):  # type: () -> CloudEnvironmentConfig
        """Return environment configuration for use in the test environment after delegation."""
        ansible_vars = dict(
            acme_host=self._get_cloud_config('acme_host'),
        )

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
        )
