# Overview

This package provides tools for applying and managing security labels in PostgreSQL databases on your Django models. This can allow you to dynamically mask specific columns to limit a user's ability to find sensitive data.

This was created with [Jay Miller](https://kjaymiller.com/) for the ["Elephant in the Room" series](https://www.youtube.com/watch?v=oSDPKT5bbuw&list=PLo6PI-0mPVLszndcJ86JStMHLibO2BHdc). The inspiration for the project was from his blog post, ["Using PostgreSQL Anonymizer to safely share data with LLMs"](https://aiven.io/blog/using-postgresql-anonymizer-to-safely-share-data-with-llms).

## Use cases

### Dynamic masking in staging

Enable the `MaskedReadsMiddleware` in your staging environment so that non-superuser staff see anonymized data while superusers see the real values. See [Customizing Masked Reads](../how-to-guides/customizing-masked-reads.md) for details.

### Static staging

Set masking labels on models without using the middleware. Clone production to staging, then use `anon.anonymize_database()` to permanently anonymize the data in the staging copy.
