import os
import sys
from pathlib import Path

from adeploy.common import colors
from adeploy.common.errors import RenderError
from adeploy.common.secret import Secret


class Watch:

    def __init__(self, provider, args, render_args, log):
        self.args = args
        self.log = log

        if 'watch' in self.args:

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
                    watcher = provider.watcher(
                        name=name,
                        src_dir=src_dir,
                        build_dir=build_dir,
                        namespaces_dir=self.args.namespaces_dir,
                        defaults_path=self.args.defaults_path,
                        args=self.args,
                        log=self.log,
                        provider=provider,
                        **vars(provider.watcher.get_parser().parse_args(render_args)))

                    self.log.info(
                        colors.green_bold('Rendering ') + colors.bold(src_dir) + ' in ' +
                        colors.bold(self.args.build_dir) + ' using the provider ' +
                        colors.bold(self.args.provider)
                    )

                    watcher.run()

                    # Clean and store secret info in build dir.
                    # Note that this affects only secrets that have been registered in the previous
                    # rendering. Secrets from deployments excluded by user filters are not stored and existing secrets
                    # won't be removed. So any testing/deployment should also explicitly respect the user filters to
                    # exclude secrets as well.
                    Secret.clean_build_secrets(build_dir)
                    for secret in Secret.get_registered():
                        secret.store(build_dir)

                except RenderError as e:
                    self.log.error(colors.red(f'Render error in source directory "{src_dir}":'))
                    self.log.error(colors.red_bold(str(e)))
                    sys.exit(1)

            if num_warnings > 0:
                self.log.warning(colors.orange(f'Rendering finished with {num_warnings} warnings'))
            else:
                self.log.info(colors.green_bold(f'Rendering finished'))

            sys.exit(0)


if __name__ == '__main__':
    pass
