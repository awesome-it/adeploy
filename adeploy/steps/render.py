import os
import sys
import argparse

from ..common import colors, RenderError


class Render:

    def __init__(self, provider, args, render_args, log):
        self.args = args
        self.log = log

        if 'render' in self.args:

            num_warnings = 0

            for src_dir in self.args.src_dirs:

                if not os.path.isdir(src_dir):
                    self.log.warning(colors.orange(f'"{src_dir}" is not a directory, skip'))
                    num_warnings += 1
                    continue

                self.log.info(
                    colors.green_bold('Rendering ') + colors.bold(src_dir) + ' in ' +
                    colors.bold(self.args.build_dir) + ' using the provider ' +
                    colors.bold(self.args.provider)
                )

                try:
                    Renderer = getattr(provider, 'Renderer')

                    renderer = Renderer(
                        src_dir=src_dir,
                        args=self.args,
                        log=self.log,
                        **vars(Renderer.get_parser().parse_args(render_args)))

                    renderer.run()

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
