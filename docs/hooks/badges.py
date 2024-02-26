from __future__ import annotations

import posixpath
import re

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from re import Match


# -----------------------------------------------------------------------------
# Hooks
# -----------------------------------------------------------------------------


def on_page_markdown(
        markdown: str, *, page: Page, config: MkDocsConfig, files: Files
):
    # Replace callback
    def replace(match: Match):
        type, args = match.groups()
        args = args.strip()
        if type == "version":
            return _badge_for_version(args, page, files)
        elif type == "provider":
            return _badge_for_provider(args, page, files)

        # Otherwise, raise an error
        raise RuntimeError(f"Unknown shortcode: {type}")

    # Find and replace all external asset URLs in current page
    return re.sub(
        r"<!-- md:(\w+)(.*?) -->",
        replace, markdown, flags=re.I | re.M
    )


# Create badge for version
def _badge_for_version(version: str, page: Page, files: Files):
    # Return badge
    icon = "material-tag-outline"
    tooltip = f"Minimum Version: {version}"
    return _badge(icon=icon, text=f"{version}", tooltip=tooltip, type="version")


# Create badge for version
def _badge_for_provider(provider: str, page: Page, files: Files):
    # Return badge
    icon = "material-cog"
    tooltip = f"Supported by {provider.capitalize()} provider"
    return _badge(icon=icon, text=provider, tooltip=tooltip, type="provider")


# Create badge
def _badge(icon: str, text: str = "", tooltip: str = "", type: str = ""):
    classes = f"mdx-badge mdx-badge--{type}" if type else "mdx-badge"
    text = f"{text}{{ data-preview='' }}" if text.endswith(")") else text
    return "".join([
        f"<span class=\"{classes}\" title=\"{tooltip}\">",
        *([f"<span class=\"mdx-badge__icon\">:{icon}:</span>"] if icon else []),
        *([f"<span class=\"mdx-badge__text\">{text}</span>"] if text else []),
        f"</span>",
    ])
