# 贡献

在编写和提交 `pull request` 前，建议先创建一个对应 `issues` 并在其中讨论相关详细信息。

## 前提准备

本指南假设您已拥有 `github` 账户，以及 `python3`，虚拟环境和 `git` 的安装配置。
但不会限制你使用的工具，比如你可以使用 `virtualenv` 代替 `pyenv`。

1. [Fork](https://github.com/shengchenyang/AyugeSpiderTools/fork) AyugeSpiderTools

2. Clone your forked repository

   ```shell
   git clone https://github.com/<username>/AyugeSpiderTools
   cd AyugeSpiderTools
   ```

3. Create a virtual environment

   ```shell
   pyenv virtualenv 3.8.5 venv
   pyenv activate venv
   pip install poetry
   poetry install
   pre-commit install
   ```

4. Run a test

   ```shell
   pytest tests/test_items.py
   ```

## 开发工作流

本项目有两个分支，分别是 `master` 和 `feature`，`master` 为稳定分支，`feature` 分支活跃度较高，通常情况下新功能及 `bug` 修复等通过此分支测试后才会最终同步到 `master` 分支。所以，若您有 `pull request` 需求请推送至 `feature` 。若您不太了解 `pull request` 流程，我会在以下部分介绍，并给出参考文章。

注意：请完成以上前提准备，以下步骤皆在你的 `repo` 中操作。

1. Checkout the `feature` branch

   ```shell
   git checkout feature
   ```

2. Create and checkout a new branch

   > 通常情况下，都不推荐直接在当前分支下操作（会影响后续与原作者的同步操作），需要新建一个新分支，如果这个分支修复了某个 `issues`，那么新建分支的名称可以为 `issue#<id>`

   比如本项目中，有一个 [issue](https://github.com/shengchenyang/AyugeSpiderTools/issues/9) 标题为 `安装后运行报错：ModuleNotFoundError: No module named 'yaml'`，假设你的 `pull request` 修复了此问题，那么新建的分支名称就可以为 `issue#9`，或者为 `fix-ModuleNotFoundError-yaml`，这里只是给出建议，具体名称可自定义，通俗易懂即可。

   ```shell
   git checkout -b <new-branch>
   ```

   以上两步也可以直接优化为一句命令 `git checkout -b <new-branch> feature`

3. Make your changes

4. Run tests

   只测试与当前 `pull request` 相关的功能即可。由于执行全部测试的依赖过多，所以你可以自行本地打包测试通过即可，可不用补充相关测试代码。

5. Commit and push your work

   ```shell
   git add .
   git commit -m "Your commit message goes here"
   git push -u origin <new-branch>
   ```

6. [Create a pull request](https://help.github.com/articles/creating-a-pull-request/)

   完成上一步后，在你 `fork` 的 `github` 项目页面上就会有创建 `pull request` 合并的按钮了， 记得要从你 `repo` 的 `<new-branch>` 分支 `pull request` 到我 `repo` 的 `feature` 中，到此已完成整个流程。
