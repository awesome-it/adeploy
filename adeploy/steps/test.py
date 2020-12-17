import os
import sys
from pathlib import Path

from adeploy.common import colors
from adeploy.common.errors import TestError
from adeploy.common.secret import Secret


class Test:

    def __init__(self, provider, args, test_args, log):
        self.args = args
        self.log = log

        if 'test' in self.args:

            num_warnings = 0

            for src_dir in self.args.src_dirs:

                src_dir = os.path.realpath(src_dir)
                name = self.args.deployment_name or os.path.basename(src_dir)
                build_dir = Path(self.args.build_dir).joinpath(self.args.provider)

                if not os.path.isdir(src_dir):
                    self.log.warning(colors.orange(f'"{src_dir}" is not a directory, skip'))
                    num_warnings += 1
                    continue

                try:
                    tester = provider.tester(
                        name=name,
                        src_dir=src_dir,
                        build_dir=build_dir,
                        namespaces_dir=self.args.namespaces_dir,
                        defaults_path=self.args.defaults_path,
                        args=self.args,
                        log=self.log,
                        **vars(provider.tester.get_parser().parse_args(test_args)))

                    self.log.info(
                        colors.green_bold('Testing ') + colors.bold(src_dir) + ' in ' +
                        colors.bold(self.args.build_dir) + ' using the provider ' +
                        colors.bold(self.args.provider)
                    )

                    tester.run()

                    # Check whether secrets have to be created
                    filters_namespace = self.args.filters_namespace
                    filter_release = self.args.filters_release
                    secrets = [] # Respect user filters
                    for secret in Secret.get_stored(build_dir, name):

                        deployment = secret.deployment
                        if (filters_namespace and deployment.namespace not in filters_namespace) or \
                                (filter_release and deployment.release not in filter_release):
                            self.log.info(f'... Secret "{colors.blue(secret.name)}" for '
                                          f'deployment "{colors.blue(deployment)}" skipped by user filter.')
                            continue

                        secrets.append(secret)
                        secret.test(self.log)

                    # Check and report orphaned secrets
                    Secret.clean_all(secrets, self.log, dry_run=True)

                except TestError as e:
                    self.log.error(colors.red(f'Test failed in source directory "{src_dir}":'))
                    self.log.error(colors.red_bold(str(e)))
                    sys.exit(1)

            if num_warnings > 0:
                self.log.warning(colors.orange(f'Testing finished with {num_warnings} warnings'))
            else:
                self.log.info(colors.green_bold(f'Testing finished'))

            sys.exit(0)


if __name__ == '__main__':
    pass
