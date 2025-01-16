.. _additional-documentation:

=====
文档
=====

贡献方式
==========

贡献的一种方式是完善此项目的文档。若您觉得文档中有需要改进的地方，可减少用户的理解成本，可通过以下方式反馈\
和 pr。

- 发现了文档中有不足或是不明了的地方，可通过提 issue 告知；
- 可以按照本文档中 :ref:`Pull Requests <additional-contributing>` 的规则来修改和提交 pr。

.. warning::

   - 若在文档方面有贡献的想法，推荐按照 Pull Requests 的规则进行；不推荐且已不支持通过文档中每个页面顶部\
     的 ``Edit on GitHub`` 的链接来修改和提交贡献；
   - 同样地，在有完善文档的想法时请先提 issue 进行简要说明，主要是避免贡献浪费。

本地构建
==========

在提交 pr 前，如何在本地查看修改后的效果呢？

1. Create a virtual environment

同样地，你可以选择自己喜欢的工具来创建当前项目的虚拟开发环境，这里以 pyenv 为例：

.. code:: bash

   pyenv local 3.9.20
   make start


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
