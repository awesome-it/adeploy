import json
import logging
import os
import sys
from pathlib import Path
from adeploy.common import colors
from adeploy.common.errors import TestError, Error, InputError


class Config:

    def __init__(self, provider, args, config_args, log):
        self.args = args
        self.log = log

        if 'config' in self.args:
            for src_dir in self.args.src_dirs:

                # Only log errors if config goes to stdout
                if not self.args.config_out:
                    self.log.setLevel(logging.WARNING)

                src_dir = os.path.realpath(src_dir)
                name = self.args.deployment_name or os.path.basename(src_dir)
                build_dir = Path(self.args.build_dir).joinpath(self.args.provider)

                if not os.path.isdir(src_dir):
                    continue

                try:
                    renderer = provider.renderer(
                        name=name,
                        src_dir=src_dir,
                        build_dir=build_dir,
                        namespaces_dir=self.args.namespaces_dir,
                        defaults_path=self.args.defaults_path,
                        args=self.args,
                        log=self.log,
                        **vars(provider.renderer.get_parser().parse_args(config_args)))

                    config = {}
                    for deployment in renderer.load_deployments():
                        config.update({deployment.release: deployment.config})

                    if not args.config_out:
                        print(json.dumps(config))
                    else:
                        with open(args.config_out, 'w+') as fd:
                            json.dump(config, fd)
                            fd.close()
                        self.log.info(f'Namespace configurations stored to "{colors.bold(args.config_out)}"')

                except Error as e:
                    self.log.error(colors.red(f'Unexpected error in source directory "{src_dir}":'))
                    self.log.error(colors.red_bold(str(e)))
                    sys.exit(1)

            sys.exit(0)


if __name__ == '__main__':
    pass
