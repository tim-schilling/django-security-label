# How Dynamic Masking Works

For information on how PostgreSQL Anonymizer implements dynamic masking, [please see their docs](https://postgresql-anonymizer.readthedocs.io/en/stable/dynamic_masking/). Dynamic masking transforms data coming out of the database at query time. Static masking will transform the data in the actual database.

This package implements dynamic masking by having the developer define the masking rules in the ``Model.Meta.indexes`` collection for any model containing sensitive information. Then a middleware must be used to switch to a masked role. The package provides two options out of the box, ``MaskedReadsMiddleware`` and ``GroupMaskingMiddleware``. See [Customizing Masked Reads](../how-to-guides/customizing-masked-reads.md) and [Group Based Masking](../how-to-guides/group-based-masking.md) for details.

The middleware needs to use ``django_security_label.middleware.set_session_role`` to change which PostgreSQL role is used for all queries during the request. By switching to a role that has masking rules applied, the database will return data from the table and dynamically transform it according to the masking rules associated with it. This allows the developer to mark the sensitive fields on the models and then determine which PostgreSQL role should be used for the given request and confidently know all data being included in that response will be anonymized according to those rules.

## PostgreSQL security labels and the `anon` provider

This package targets [PostgreSQL's ``SECURITY LABEL``](https://www.postgresql.org/docs/current/sql-security-label.html) API, which is what PostgreSQL Anonymizer utilizes.

Security labels are database schema that can be associated with a particular schema object, such as a table or column.

By default, PostgreSQL Anonymizer creates the ``anon`` provider. This package defaults to using that. If more than one masking policy/provider is desired for an object, a new provider must be created. In this case, it seems to make sense to have one PostgreSQL role per provide/policy. An example of this can be seen in the code for the ``setup_policies`` management command and is how ``GroupMaskingMiddleware`` works.

## Session role switching

This package relies on the middleware using the [``SET SESSION ROLE ... ;`` SQL syntax](https://www.postgresql.org/docs/current/sql-set-role.html) to switch roles to process a request. It is important that the middleware reset the role before finishing processing the response.

## The `dsl_masked_reader` role

The package will create a new role (what a PostgreSQL calls a user) in the database. This user will inherit all the properties of the user used for the database connection in the ``DATABASES`` setting. By inheriting from the user, it allows the reader role to mutate non-masked tables. This role is created with ``NOLOGIN`` so it can only be switched to.
