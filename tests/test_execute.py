import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.mark import Mark
from _pytask.nodes import FilePathNode
from conftest import needs_latexmk
from conftest import skip_on_github_actions_with_win
from pytask import cli
from pytask import main
from pytask_latex.execute import pytask_execute_task_setup


class DummyTask:
    pass


@pytest.mark.unit
@pytest.mark.parametrize(
    "depends_on, produces, expectation",
    [
        (
            [FilePathNode("a", Path("a.tex"))],
            [FilePathNode("a", Path("a.pdf"))],
            does_not_raise(),
        ),
        (
            [FilePathNode("a", Path("a.txt")), FilePathNode("b", Path("b.pdf"))],
            [FilePathNode("a", Path("a.pdf"))],
            pytest.raises(ValueError),
        ),
        (
            [FilePathNode("a", Path("a.tex"))],
            [FilePathNode("a", Path("a.dvi"))],
            does_not_raise(),
        ),
        (
            [FilePathNode("a", Path("a.tex"))],
            [FilePathNode("a", Path("a.ps"))],
            does_not_raise(),
        ),
        (
            [FilePathNode("a", Path("a.tex"))],
            [FilePathNode("a", Path("a.txt"))],
            pytest.raises(ValueError),
        ),
        (
            [FilePathNode("a", Path("a.tex"))],
            [FilePathNode("a", Path("a.txt")), FilePathNode("b", Path("b.pdf"))],
            pytest.raises(ValueError),
        ),
    ],
)
def test_pytask_execute_task_setup(monkeypatch, depends_on, produces, expectation):
    # Act like latexmk is installed since we do not test this.
    monkeypatch.setattr("pytask_latex.execute.shutil.which", lambda x: True)

    task = DummyTask()
    task.depends_on = depends_on
    task.produces = produces
    task.markers = [Mark("latex", (), {})]

    with expectation:
        pytask_execute_task_setup(task)


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_compile_latex_document(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on("document.tex")
    @pytask.mark.produces("document.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    I was tired of my lady
    \end{document}
    """
    tmp_path.joinpath("document.tex").write_text(textwrap.dedent(latex_source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
    assert tmp_path.joinpath("document.pdf").exists()


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_compile_latex_document_to_different_name(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on("in.tex")
    @pytask.mark.produces("out.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    We'd been together too long
    \end{document}
    """
    tmp_path.joinpath("in.tex").write_text(textwrap.dedent(latex_source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
    assert tmp_path.joinpath("out.pdf").exists()


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_compile_w_bibiliography(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on(["in_w_bib.tex", "bib.bib"])
    @pytask.mark.produces("out_w_bib.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \usepackage{natbib}
    \begin{document}
    \cite{pytask}
    \bibliographystyle{plain}
    \bibliography{bib}
    \end{document}
    """
    tmp_path.joinpath("in_w_bib.tex").write_text(textwrap.dedent(latex_source))

    bib_source = r"""
    @Article{pytask,
      author = {Tobias Raabe},
      title  = {pytask},
      year   = {2020},
    }
    """
    tmp_path.joinpath("bib.bib").write_text(textwrap.dedent(bib_source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
    assert tmp_path.joinpath("out_w_bib.pdf").exists()


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_raise_error_if_latexmk_is_not_found(tmp_path, monkeypatch):
    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on("document.tex")
    @pytask.mark.produces("document.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    Ein Fuchs muss tun, was ein Fuchs tun muss. Luxus und Ruhm und rulen bis zum
    Schluss.
    \end{document}
    """
    tmp_path.joinpath("document.tex").write_text(textwrap.dedent(latex_source))

    # Hide latexmk if available.
    monkeypatch.setattr("pytask_latex.execute.shutil.which", lambda x: None)

    session = main({"paths": tmp_path})

    assert session.exit_code == 1
    assert isinstance(session.execution_reports[0].exc_info[1], RuntimeError)


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_compile_latex_document_w_xelatex(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.latex(["--xelatex", "--interaction=nonstopmode", "--synctex=1"])
    @pytask.mark.depends_on("document.tex")
    @pytask.mark.produces("document.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    I got, I got, I got, I got loyalty, got royalty inside my DNA.
    \end{document}
    """
    tmp_path.joinpath("document.tex").write_text(textwrap.dedent(latex_source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
    assert tmp_path.joinpath("document.pdf").exists()


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_compile_latex_document_w_two_dependencies(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on(["document.tex", "in.txt"])
    @pytask.mark.produces("document.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    Mother earth is pregnant for the third time.
    \end{document}
    """
    tmp_path.joinpath("document.tex").write_text(textwrap.dedent(latex_source))

    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
    assert tmp_path.joinpath("document.pdf").exists()


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_fail_because_latex_document_is_not_first_dependency(tmp_path):
    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on(["in.txt", "document.tex"])
    @pytask.mark.produces("document.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    For y'all have knocked her up
    \end{document}
    """
    tmp_path.joinpath("document.tex").write_text(textwrap.dedent(latex_source))

    tmp_path.joinpath("in.txt").touch()

    session = main({"paths": tmp_path})

    assert session.exit_code == 3
    assert isinstance(session.collection_reports[0].exc_info[1], ValueError)


@needs_latexmk
@skip_on_github_actions_with_win
@pytest.mark.end_to_end
def test_compile_document_to_out_if_document_has_relative_resources(tmp_path):
    """Test that motivates the ``"--cd"`` flag.

    If you have a document which includes other resources via relative paths and you
    compile the document to a different output folder, latexmk will not find the
    relative resources. Thus, use the ``"--cd"`` flag to enter the source directory
    before the compilation.

    """
    tmp_path.joinpath("sub", "resources").mkdir(parents=True)

    task_source = """
    import pytask

    @pytask.mark.latex
    @pytask.mark.depends_on(["document.tex", "resources/content.tex"])
    @pytask.mark.produces("out/document.pdf")
    def task_compile_document():
        pass

    """
    tmp_path.joinpath("sub", "task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = r"""
    \documentclass{report}
    \begin{document}
    \input{resources/content}
    \end{document}
    """
    tmp_path.joinpath("sub", "document.tex").write_text(textwrap.dedent(latex_source))

    resources = r"""
    In Ottakring, in Ottakring, wo das Bitter so viel süßer schmeckt als irgendwo in
    Wien.
    """
    tmp_path.joinpath("sub", "resources", "content.tex").write_text(resources)

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.tasks) == 1
