# Contributing to Stone
We value and rely on the feedback from our community. This comes in the form of bug reports, feature requests, and general guidance. We welcome your issues and pull requests and try our hardest to be timely in both response and resolution. Please read through this document before submitting issues or pull requests to ensure we have the necessary information to help you resolve your issue.

## Filing Bug Reports
You can file a bug report on the [GitHub Issues][issues] page.

1. Search through existing issues to ensure that your issue has not been reported. If it is a common issue, there is likely already an issue.

2. Please ensure you are using the latest version of Stone. While this may be a valid issue, we only will fix bugs affecting the latest version and your bug may have been fixed in a newer version.

3. Provide as much information as you can regarding the language version, Stone version, and any other relevant information about your environment so we can help resolve the issue as quickly as possible.

## Submitting Pull Requests

We are more than happy to receive pull requests helping us improve the state of our SDK. You can open a new pull request on the [GitHub Pull Requests][pr] page.

1. Please ensure that you have read the [License][license], [Code of Conduct][coc] and have signed the [Contributing License Agreement (CLA)][cla].

2. Please add tests confirming the new functionality works. Pull requests will not be merged without passing continuous integration tests unless the pull requests aims to fix existing issues with these tests.

## Testing the Code

Tests live under the `test/` folder. They can be run by running the following command:

```
$ python setup.py test
```

They can also be run as a part of `tox` and they should be ran in a virtual environment to ensure isolation of the testing environment.

[issues]: https://github.com/dropbox/stone/issues
[pr]: https://github.com/dropbox/stone/pulls
[coc]: https://github.com/dropbox/stone/blob/main/CODE_OF_CONDUCT.md
[license]: https://github.com/dropbox/stone/blob/main/LICENSE
[cla]: https://opensource.dropbox.com/cla/