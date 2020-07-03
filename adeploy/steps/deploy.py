import os
import sys

from ..common import colors, DeployError


class Deploy:

    def __init__(self, provider, args, deploy_args, log):
        self.args = args
        self.log = log

        if 'deploy' in self.args:

            num_warnings = 0

            for src_dir in self.args.src_dirs:

                src_dir = os.path.realpath(src_dir)

                if not os.path.isdir(src_dir):
                    self.log.warning(colors.orange(f'"{src_dir}" is not a directory, skip'))
                    num_warnings += 1
                    continue

                self.log.info(
                    colors.green_bold('Deploying ') + colors.bold(src_dir) + ' in ' +
                    colors.bold(self.args.build_dir) + ' using the provider ' +
                    colors.bold(self.args.provider)
                )

                try:
                    Deployer = getattr(provider, 'Deployer')

                    deployer = Deployer(
                        src_dir=src_dir,
                        args=self.args,
                        log=self.log,
                        **vars(Deployer.get_parser().parse_args(deploy_args)))

                    deployer.run()

                except DeployError as e:
                    self.log.error(colors.red(f'Deployment failed in source directory "{src_dir}":'))
                    self.log.error(colors.red_bold(str(e)))
                    sys.exit(1)

            if num_warnings > 0:
                self.log.warning(colors.orange(f'Deployment finished with {num_warnings} warnings'))
            else:
                self.log.info(colors.green_bold(f'Deployment finished'))

            sys.exit(0)


if __name__ == '__main__':
    pass
