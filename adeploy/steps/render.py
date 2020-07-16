import os
import sys
from pathlib import Path

from adeploy.common import colors, RenderError
from adeploy.common.secret import get_secrets


class Render:

    def __init__(self, provider, args, render_args, log):
        self.args = args
        self.log = log

        if 'render' in self.args:

            num_warnings = 0

            for src_dir in self.args.src_dirs:

                src_dir = os.path.realpath(src_dir)
                build_dir = Path(self.args.build_dir).joinpath(self.args.provider)

                if not os.path.isdir(src_dir):
                    self.log.warning(colors.orange(f'"{src_dir}" is not a directory, skip'))
                    num_warnings += 1
                    continue

                try:
                    renderer = provider.renderer(
                        name=self.args.deployment_name or os.path.basename(src_dir),
                        src_dir=src_dir,
                        build_dir=build_dir,
                        namespaces_dir=self.args.namespaces_dir,
                        defaults_path=self.args.defaults_path,
                        args=self.args,
                        log=self.log,
                        **vars(provider.renderer.get_parser().parse_args(render_args)))

                    self.log.info(
                        colors.green_bold('Rendering ') + colors.bold(src_dir) + ' in ' +
                        colors.bold(self.args.build_dir) + ' using the provider ' +
                        colors.bold(self.args.provider)
                    )

                    renderer.run()

                    # Render secrets
                    for secret in get_secrets():
                        secret.render(build_dir, self.log)

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
