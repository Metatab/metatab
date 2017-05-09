
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



Create S3 Users
---------------

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

The secret key and access key should be given to the user, to set up as according to the next
 section.

Setup S3 Credentials
--------------------

The access and secret keys should be stored in a boto configuration file, such as ``~/.aws/credentials``. See
the `boto3 configuration documentation <http://boto3.readthedocs.io/en/latest/guide/configuration.html>`_ for details. Here is an example of a ``credentials`` file

.. code-block::

    [default]
    aws_access_key_id = AKIAJXMFAP3X5TRYYQ5Q
    aws_secret_access_key = b81zw4LRDKVILzrZbS0B8KMn88xbY9BEEnwzKrz2


If you have multiple credentials, you can put them in different sections by changing ``[default]`` to the name of another profile. For instance, here is a credentials file with a default and alternate profile:

.. code-block::

    [default]
    aws_access_key_id = AKIAJXMFAP3X5TRYYQ5Q
    aws_secret_access_key = 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
    [fooprofile]
    aws_access_key_id = AKIAX5TRYYQ5QJXMFAP3
    aws_secret_access_key = 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

To use the alternate credentials with the ``metasync`` program, use the ``-p`` option:

.. code-block:: bash

    $ metasync -p fooprofile -S library.metatab.org

To use the alternate credentials with the ``open_package()`` function, you will need to set them in the shell before you run any programs. The ``metasync -C`` program will display the credentials in a form that can be shell eval'd, and the ``-p`` option can select an alternate profile.

.. code-block:: bash

    $ metasync -C -p fooprofile
    export AWS_ACCESS_KEY_ID=AKIAX5TRYYQ5QJXMFAP3
    export AWS_SECRET_ACCESS_KEY=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
    # Run  'eval $(metasync -C -p fooprofile )' to configure credentials in a shell

The last line of the output shows the command to run to set the credentials in the shell:

.. code-block:: bash

    $ eval $(metasync -C -p fooprofile )

Setting credentials in the shell is only required if you use a
