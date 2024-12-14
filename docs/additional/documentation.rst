.. _additional-documentation:

=====
文档
=====

贡献方式
==========

贡献的一种方式是完善此项目的文档。若您觉得文档中有需要改进的地方，可减少用户的理解成本，可通过以下方式反馈\
和 pr。

- 文档中每个页面顶部都有一个 ``Edit on GitHub`` 的链接。通过单击该链接，您可以创建包含更改的拉取请求。\
  您需要一个 Github 帐户才能编辑页面。
- 但我还是推荐按照 `Pull Requests`_ 的规则来修改和提交 pr。

.. warning::

   同样地，在有完善文档的想法时请先提 issue 进行简要说明，主要是避免贡献浪费。

本地构建
==========

在提交 pr 前，如何在本地查看修改后的效果呢？

1. Create a virtual environment

.. code:: bash

   pyenv virtualenv 3.9.20 venv
   pyenv activate venv
   pip install poetry
   poetry install
   pre-commit install


2. Make changes

   在 docs 文件夹下修改您关心的部分。

3. Check the effect
::

   # 进入文档目录
   cd docs

   # 构建文档
   make html

.. note::

   当构建完成时使用浏览器访问本项目中 ``docs/_build/html/index.html`` 即可查看修改后的效果。

.. _Pull Requests: https://ayugespidertools.readthedocs.io/en/latest/additional/contributing.html
