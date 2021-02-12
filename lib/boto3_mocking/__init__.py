# Copyright 2021 Richard T. Weeks
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .version import __version__
from unittest.mock import patch
import boto3
from contextlib import contextmanager

class UnpatchedAccess(Exception):
    """Raised when an AWS service is accessed without a registered handler"""

class AlreadyPatched(Exception):
    """Raised on registration of a handler for an AWS service for which a handler is already present"""

class FirstRegistration(Exception):
    """Saved to track successful registration of a handler
    
    This is used as the :attr:`cause` of the :class:`AlreadyPatched` exception
    raised on the second call to register a handler for the same service.
    """

class PatchTarget:
    def __init__(self, name: str):
        super().__init__()
        self.name, self.real = name, getattr(boto3, name)
        self.services = {}
        self.registrations = {}
        self.allowed = set()
    
    def dispatch(self, service: str, **kwargs):
        if service in self.services:
            return self.services[service](**kwargs)
        
        if service in self.allowed:
            return self.real(service, **kwargs)
        
        raise UnpatchedAccess(service)
    
    def register_handler(self, service: str, handler):
        if service in self.services:
            raise AlreadyPatched(service) from self.registrations.get(service)
        
        try:
            self.services[service] = handler
            raise FirstRegistration(service)
        except FirstRegistration as ex:
            self.registrations[service] = ex
    
    @contextmanager
    def handler_for(self, service: str, handler):
        with patch.dict(self.services, {service: handler}):
            yield

clients = PatchTarget('client')
resources = PatchTarget('resource')

boto3.boto3_mocking_patched = False

patching = patch.multiple(
    boto3,
    boto3_mocking_patched=True,
    client=clients.dispatch,
    resource=resources.dispatch,
)

def enter_handlers(stack, service: str, **kwargs):
    """Enter multiple mock handler patching contexts
    
    *stack* is intended to be a :class:`contextlib.ExitStack`.
    
    Entries in *kwargs* should be names of :class:`.PatchTarget` instances on
    this module.
    """
    for target_name, handler in kwargs.items():
        stack.enter_context(
            globals()[target_name].handler_for(service, handler)
        )

def engage_patching():
    if not patching_engaged():
        patching.start()

def patching_engaged() -> bool:
    return boto3.boto3_mocking_patched
