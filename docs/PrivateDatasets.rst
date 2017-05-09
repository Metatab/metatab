
Private Datasets
================

Datasets that should be protected from unauthorized access can be written to S3 with a private ACL and access using S3 credentials. To use private datasets:

- Use the **metaaws** program to setup an S3 bucket with a policy and users
- Add a ``Root.Access`` term to the dataset's metatab document.
- Syncronize the dataset to s3 with **metasync**
- Setup credentials for an S3 user
- Access the dataset using an S3 url.

Setup The S3 Bucket
-------------------

Suppose we want to store datasets in a bucket ``bucket.example.com``. After creating the bucjet, initialize it with subdirectories and policies with the **metaaws**  program.

.. code-block:: bash

    $ metaaws init-bucket bucket.example.com



Configure and Sync a Dataset
----------------------------

To make a dataset private,  add a ``Root.Access`` term to the ``Root`` section, with  a value of ``private``


Setup S3 Credentials
--------------------

Use the **metaaws**  program to create users and add permissions to the bucket. First, initialize a bucket with the apprpriate policies:

.. code-block:: bash

    $ metaaws init-bucket bucket.example.com

Then, create a new user.

.. code-block:: bash

    $ metaaws new-user foobar
    Created user : foobar
    arn          : arn:aws:iam::095555823111:user/metatab/foobar
    Access Key   : AKIAJXMFAP3X5TRYYQ5Q
    Secret Key   : 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

The access and secret keys should be stored in a boto configuration file, such as ``~/.aws/credentials``. See
the `boto3 configuration documentation <http://boto3.readthedocs.io/en/latest/guide/configuration.html>`_ for details.

.. code-block::

    [default]
    aws_access_key_id = AKIAJXMFAP3X5TRYYQ5Q
    aws_secret_access_key = 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