"""Custom macros for mkdocs-macros-plugin."""
from pathlib import Path


def define_env(env):
    @env.macro
    def readme_section(start, end):
        """Return the slice of README.md between two heading strings."""
        readme = (Path(env.conf["docs_dir"]).parent / "README.md").read_text()
        start_idx = readme.find(start)
        end_idx = readme.find(end, start_idx)
        return readme[start_idx:end_idx].rstrip()
