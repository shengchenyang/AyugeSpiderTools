.. _intro-install:

==========
安装指南
==========

支持的 Python 版本
===================

AyugeSpiderTools 需要 Python 3.9+。

.. warning::

   在 AyugeSpiderTools 3.10.1 之后的版本不再支持 python 3.8。

安装 AyugeSpiderTools
=======================

   可以使用以下命令安装 ayugespidertools 及其依赖项：

1. 若你的数据库场景只需要 mysql 和 mongodb，且不需要本库 extras 中的扩展功能，那么直接简洁安装即可，\
命令如下：

.. code:: bash

   pip install ayugespidertools

2. 若你需要更多的数据库场景，且同样不需要本库 extras 中的扩展功能，那么安装数据库版本最好，命令如下：

.. code:: bash

   pip install ayugespidertools[database]

3. 安装全部依赖命令如下：

.. code:: bash

   pip install ayugespidertools[all]

4. 安装预发布(开发)版本，通过源码安装：

.. code:: bash

   # 请注意，此源码方式安装的是开发版本，请勿在正式场景中使用！
   pip install git+https://github.com/shengchenyang/AyugeSpiderTools.git

.. note::

   若你只需要 scrapy 扩展库的简单功能，那么默认的简洁依赖安装即可；一些可选择的开发功能（都会放在 extras \
   部分）若要使用，请使用完整安装。

   强烈建议您将 ayugespidertools 安装在专用的 virtualenv 中，以避免与您的系统包发生冲突。

可能遇到的问题
---------------

   在安装时可能会遇到以下问题：

- zsh: no matches found: ayugespidertools[database]

.. code:: bash

     # zsh 中需要修改对应的命令
     pip install 'ayugespidertools[database]'
     pip install 'ayugespidertools[all]'

- 无法安装到最新版本

这是国内源对第三方库同步(完整度和速度)的问题。
::

   # 1.首先查看 pypi 上的版本信息
   # 如果输出的 latest 版本信息非最新，说明你的 pip 的 pypi 源还未同步，可选择“科学上网”或手动安装。
   pip index versions ayugespidertools

   # 1.1. 若你可以科学访问，安装只需指定 pypi 官方源即可：
   pip install ayugespidertools -i https://pypi.org/simple

   # 1.2. 若访问受限，则需要手动安装：
   # 先到 https://pypi.org/project/AyugeSpiderTools/#files 或
   # https://github.com/shengchenyang/AyugeSpiderTools/releases 下载 whl 文件
   # 然后 pip 安装此 whl 即可
   pip install ayugespidertools-x.x.x-py3-none-any.whl[database] -i https://mirrors.aliyun.com/pypi/simple/
   # zsh 中的命令同样需要修改
   pip install 'ayugespidertools-x.x.x-py3-none-any.whl[database]' -i https://mirrors.aliyun.com/pypi/simple/

- 无法查找到 ayugespidertools

  这也是国内源的完整度问题，推荐优先配置为阿里云源或者清华大学源即可，若还不行请切换到官方源。

报错详情如下：
::

   ERROR: Could not find a version that satisfies the requirement ayugespidertools (from versions: none)
   ERROR: No matching distribution found for ayugespidertools

解决方法如下：
::

   pip install ayugespidertools -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
   # 或者使用官方源：
   pip install ayugespidertools -i https://pypi.org/simple

- 可能存在的兼容问题

  特别是 Apple Silicon MacOS 的较新系统场景，若遇到安装问题，可先尝试单独安装 Scrapy，若问题依然存在\
  则可排除本库的问题。

报错示例如下：
::

   ImportError: dlopen(/Users/runner/work/AyugeSpiderTools/AyugeSpiderTools/.tox/py/lib/python3.8/site-packages/lxml/etree.cpython-38-darwin.so, 0x0002): symbol not found in flat namespace '_exsltDateXpathCtxtRegister'
   /Users/runner/work/AyugeSpiderTools/AyugeSpiderTools/.tox/py/lib/python3.8/site-packages/coverage/control.py:887: CoverageWarning: No data was collected. (no-data-collected)

解决方法如下：
::

   可能出现兼容问题的库有：lxml, urllib3, twisted 等，可通过手动安装未报错的依赖版本，或升级 Python\
   Patch 版本来快速解决。

若遇到其它的各种问题，请提 `issues`_ 反馈。

值得知道的事情
----------------

- ayugespidertools 是依赖于 Scrapy 开发的，对其在爬虫开发中遇到的常用操作进行扩展。
- 可以从最新源码中构建，构建方法请参考本文 :ref:`How-To-Build-Your-Own-Library <diy-myself>` 部分。

使用虚拟环境（推荐）
--------------------

建议在所有平台上的虚拟环境中安装此库。

有关如何创建虚拟环境的信息，请参阅 `虚拟环境和包`_ 部分。

.. _issues: https://github.com/shengchenyang/AyugeSpiderTools/issues/new/choose
.. _虚拟环境和包: https://docs.python.org/3/tutorial/venv.html#tut-venv
