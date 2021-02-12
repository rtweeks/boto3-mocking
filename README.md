# Boto3-Mocking - Centralized Mocking of Boto3 for Testing

When testing code that accesses AWS through the `boto3` library, it is often
desirable to isolate the code from actual access to the AWS API.  This library
facilitates both that and dispatch of the service requests to mock
implementations.

## Install

```console
$ pip install boto3-mocking
```

## Usage

### Engaging the Patches

Two options exist to engage the patching of `boto3`: permanent and contextual.  To permanently patch `boto3` within the process, somewhere in the testing code that precedes use of the `boto3.client` and `boto3.resource` functions, use this code:

```python
import boto3_mocking
boto3_mocking.engage_patching()
```

**NOTE** If your mainline code constructs `boto3` clients or resources when it loads, then it is critical for the test harness to engage patching before loading mainline code.

To temporarily patch `boto3`, use this code:

```python
import boto3_mocking
with boto3_mocking.patching:
    ...your code accessing AWS here...
```

### Testing for Patch Engagement

This package exposes a function to test whether patching is currently engaged.  Use this in your testing code before doing something that would harm or be expensive on the actual AWS environment:

```python
import boto3_mocking
if not boto3_mocking.patching_engaged():
    raise Exception("...")
```

### Registering a Service Handler

Service handlers can either be registered permanently or contextually.  Registration is managed through `boto3_mocking.clients` and `boto3_mocking.resources`, corresponding to `boto3.client` and `boto3.resource`.  A service handler (whether for a client or a resource) is a callable that accepts arguments by keyword and returns the mock client or resource as appropriate.  The handler should accept the same keywords as the client or service it substitutes.  Registering a mock client *does not* automatically mock a corresponding resource, as the resource does not use `boto3.client` to construct/obtain its client object.

To permanently register a client handler for the `'cognito-idp'` service, the code would look like:

```python
import boto3_mocking
boto3_mocking.clients.register_handler('cognito-idp', MockCognitoIdpClient)
```

Handlers can also be contextually registered:

```python
import boto3_mocking
with boto3_mocking.resources.handler_for('ec2', MockEC2Resource):
    ...your code accessing EC2 here...
```

Only one handler may be permanently registered for each service, but a contextually registered handler registration does override a permanently registered one for the same service during its context without error or warning.

### Accessing Real Boto3 Functionality

`boto3_mocking.clients` and `boto3_mocking.resources` both provide a `real` attribute holding the original function from `boto3` from before the patching is engaged.  Your service handlers can make use of these functions if necessary.  One example would be to redirect `'dynamodb'` clients and resources to a DynamoDBLocal instance, where the actual `boto3` library is still needed but needs to have certain keyword arguments (`endpoint_url` and `use_ssl`) included when the client or resource is created.

### The Allowed Lists

Access to the real functionality of `boto3` can be allowed service-by-service in both `boto3_mocking.clients` and `boto3_mocking.resources` via their `allowed` set.  Just `add` the name of the service to `boto3_mocking.clients.allowed` or `boto3_mocking.resources.allowed` to allow those calls without a registered handler.

### Access to Unhandled Services

If a service client or resource is accessed without a handler, `boto3_mocking` raises a `boto3_mocking.UnpatchedAccess` exception unless the service is in the respective `allowed` list.


## License

This code is licensed under Apache License 2.0.  Please see `LICENSE` for full text.

## Contributing

1. Fork it on GitHub (https://github.com/rtweeks/boto3-mocking)
1. Create your feature branch (`git checkout -b my-new-feature`)
1. Commit your changes (`git commit -am 'Add some feature'`)
1. Push to the branch (`git push origin my-new-feature`)
1. Create a new Pull Request (on [GitHub](https://github.com))
