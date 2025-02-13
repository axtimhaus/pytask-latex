"""This module contains compilation steps for compiling a LaTeX document.

Each compilation step must have the following signature:

.. code-block::

    def compilation_step(path_to_tex: Path, path_to_document: Path):
        ...

A compilation step constructor must yield a function with this signature.

"""
from __future__ import annotations

import subprocess

from pytask_latex.path import relative_to
from pytask_latex.utils import to_list


def latexmk(options=("--pdf", "--interaction=nonstopmode", "--synctex=1", "--cd")):
    """Compilation step that calls latexmk."""
    options = [str(i) for i in to_list(options)]

    def run_latexmk(path_to_tex, path_to_document):
        job_name_opt = [f"--jobname={path_to_document.stem}"]
        out_dir_opt = [
            f"--output-directory={relative_to(path_to_tex, path_to_document.parent)}"
        ]
        cmd = (
            ["latexmk", *options]
            + job_name_opt
            + out_dir_opt
            + [path_to_tex.as_posix()]
        )
        subprocess.run(cmd, check=True)

    return run_latexmk
