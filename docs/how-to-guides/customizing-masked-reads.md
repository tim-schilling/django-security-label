# Customizing Masked Reads

The default configuration of this package uses dynamic masking. This is because static masking will irrevocably destroy your database's data. While this is a valuable tool for some staging environments, it's not the goal at the moment.

The challenge is to use a different database role when we need to have masked reads. This is why we create the ``dsl_masked_reader`` role. We can switch to this role with ``SET SESSION ROLE dsl_masked_reader;`` and ``ROLE RESET;`` to enable and disable masked reads respectively.

The middleware, ``MaskedReadsMiddleware`` controls when the role is switched. It does so crudely at this point by only allowing ``user.is_superuser`` users to use the default database role. All other queries will use the ``dsl_masked_reader`` role and be subject to the security labels that were defined on the columns.

## Writing your own middleware

Please copy and update the code in ``MaskedReadsMiddleware`` to suit your needs. The majority of the complexity will be in your definition of `use_masked_reads`.

For example, if you only wanted to force anonymous users to have masked reads:

```python
from __future__ import annotations

from django.db import connection
from django.http import HttpRequest
from django_security_label.middleware import enable_masked_reads, disable_masked_reads


def use_masked_reads(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return user is None or not user.is_authenticated


class AnonymousOnlyMaskedReadsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if enable_masking := use_masked_reads(request):
            enable_masked_reads()

        response = self.get_response(request)

        if enable_masking:
            disable_masked_reads()

        return response
```
