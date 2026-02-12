# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/tim-schilling/django-security-label/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                            |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/django\_security\_label/\_\_init\_\_.py                                     |        3 |        0 |        0 |        0 |    100% |           |
| src/django\_security\_label/apps.py                                             |       38 |        0 |       14 |        2 |     96% |22->21, 59->64 |
| src/django\_security\_label/compat.py                                           |        6 |        0 |        2 |        0 |    100% |           |
| src/django\_security\_label/constants.py                                        |        2 |        0 |        0 |        0 |    100% |           |
| src/django\_security\_label/labels.py                                           |      116 |        0 |        2 |        0 |    100% |           |
| src/django\_security\_label/management/\_\_init\_\_.py                          |        0 |        0 |        0 |        0 |    100% |           |
| src/django\_security\_label/management/commands/\_\_init\_\_.py                 |        0 |        0 |        0 |        0 |    100% |           |
| src/django\_security\_label/management/commands/create\_anonymizer\_policies.py |       16 |        0 |        0 |        0 |    100% |           |
| src/django\_security\_label/middleware.py                                       |       29 |        0 |        2 |        0 |    100% |           |
| src/django\_security\_label/migrations/0001\_initial.py                         |       14 |        2 |        0 |        0 |     86% |     17-18 |
| src/django\_security\_label/migrations/\_\_init\_\_.py                          |        0 |        0 |        0 |        0 |    100% |           |
| src/django\_security\_label/operations.py                                       |       39 |        0 |        4 |        0 |    100% |           |
| tests/\_\_init\_\_.py                                                           |        0 |        0 |        0 |        0 |    100% |           |
| tests/settings.py                                                               |        7 |        0 |        0 |        0 |    100% |           |
| tests/test\_create\_anonymizer\_policies.py                                     |       42 |        1 |        4 |        1 |     96% |        22 |
| tests/test\_labels.py                                                           |       75 |        0 |        0 |        0 |    100% |           |
| tests/test\_makemigrations.py                                                   |       38 |        0 |        0 |        0 |    100% |           |
| tests/test\_middleware.py                                                       |       78 |        0 |        0 |        0 |    100% |           |
| tests/test\_operations.py                                                       |       63 |        0 |        0 |        0 |    100% |           |
| tests/test\_sqlmigrate.py                                                       |       40 |        0 |        0 |        0 |    100% |           |
| tests/testapp/\_\_init\_\_.py                                                   |        0 |        0 |        0 |        0 |    100% |           |
| tests/testapp/apps.py                                                           |        5 |        0 |        0 |        0 |    100% |           |
| tests/testapp/middleware.py                                                     |       17 |        3 |        2 |        0 |     84% |     21-23 |
| tests/testapp/migrations/0001\_initial.py                                       |        8 |        0 |        0 |        0 |    100% |           |
| tests/testapp/migrations/\_\_init\_\_.py                                        |        0 |        0 |        0 |        0 |    100% |           |
| tests/testapp/models.py                                                         |       12 |        0 |        0 |        0 |    100% |           |
| tests/utils.py                                                                  |       37 |        0 |        0 |        0 |    100% |           |
| **TOTAL**                                                                       |  **685** |    **6** |   **30** |    **3** | **99%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/tim-schilling/django-security-label/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/tim-schilling/django-security-label/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/tim-schilling/django-security-label/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/tim-schilling/django-security-label/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Ftim-schilling%2Fdjango-security-label%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/tim-schilling/django-security-label/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.