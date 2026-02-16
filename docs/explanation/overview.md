# Overview

This package provides tools for applying and managing security labels in PostgreSQL databases on your Django models. Combined with the [PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/en/stable/) extension, this can allow you to mask columns to limit exposure of sensitive data.

This was created with [Jay Miller](https://kjaymiller.com/) for the ["Elephant in the Room" series](https://www.youtube.com/watch?v=oSDPKT5bbuw&list=PLo6PI-0mPVLszndcJ86JStMHLibO2BHdc). The inspiration for the project was from his blog post, ["Using PostgreSQL Anonymizer to safely share data with LLMs"](https://aiven.io/blog/using-postgresql-anonymizer-to-safely-share-data-with-llms).

## Why define masking rules in models

This package is not necessary to utilize the PostgreSQL Anonymizer package. However, it does allow a project to specify the masking rules as a part of the models. When a field is added to a model, it is generally known whether that field will contain sensitive information. By specifying the masking rule on the model, the data coming out of that underlying table will be masked without having to change the rest of the application logic.

Similarly, this means changing those masking rules is significantly more straightforward than having to edit views or service layer to use masking.

### Constraints

This package isn't without its constraints.

#### Index hack

This package is a bit of a hack in that it hijacks the ``Index`` feature to run custom SQL after the table has been created. While this is entirely valid and is proven to work in tests, it would be better if Django's migrations better supported column specific schema. [Jacob Walls has identified some work](https://forum.djangoproject.com/t/can-the-migration-system-be-extended-by-third-party-apps/44009/4) that seems to be reasonable.

#### Lack of clean-up on setup_roles

The ``GroupMaskingMiddleware`` requires a user to run the ``setup_roles`` management command. This creates new roles in the database and marks them as masked for the relevant security label provider. These changes will only update the mentioned roles. If a role is removed, you must remove that role from each of your environments that is exists on. These roles are created with the ``NOLOGIN`` option, so it's unlikely they do anything other than add noise when looking at your database. That said, it's
an area of improvement for this package.


## Use cases

### Dynamic masking

The primary use case of this package is to [dynamically mask data](https://postgresql-anonymizer.readthedocs.io/en/stable/dynamic_masking/). The package allows you to define which fields on your model have sensitive data and when access to them should be limited.

The simplest option is to use ``MaskedReadsMiddleware`` so that non-superuser staff see anonymized data while superusers see the real values. See [Customizing Masked Reads](../how-to-guides/customizing-masked-reads.md) for details.

You can customize your own implementing your own middleware that functions similarly to ``MaskedReadsMiddleware`` based on your needs. The two important aspects to keep in mind is to determine which PostgreSQL role should be used, switch to it with ``django_security_label.middleware.set_session_role`` and switch back to the ``DATABASES`` role by using ``django_security_label.middleware.disable_masked_reads()``. See the following code for an example:

```python
set_session_role(some_role)
try:
    response = self.get_response(request)
except InternalError:
    disable_masked_reads()
    raise
disable_masked_reads()
return response
```

#### Constraints

The biggest challenge with dynamic masking is that if the PostgreSQL role that's being used has any masking rule in effect for the table, that role will only be able to select data from the table. This means that creates, updates and deletes will fail. This is a byproduct of dynamic masking with PostgreSQL Anonymizer.

### Static masking

[Static masking](https://postgresql-anonymizer.readthedocs.io/en/stable/static_masking/#) transforms the actual data in the database according to the masking rules defined on the table. This means it's a destructive action and should only be used in non-production environments.

It should be possible to utilize this package with static masking. This is because the masking rules are defined in the models and are applied via migrations.

Static masking can be used by cloning the production database (that is up to date on migrations), then connecting to the non-production database and running the SQL, ``SELECT anon.anonymize_database();``. In this case, no middleware is necessary and all users would be able to mutate all data.

### Compliance considerations

This package assumes that the people managing your environments can be trusted with the data. This package can't be used to secure sensitive data if the developer can simply fake the migration, change the middleware, or connect to the database directly. If you are using this to limit developers' access to sensitive data, carefully consider who has the ability to access what information and what they can change without oversight.
