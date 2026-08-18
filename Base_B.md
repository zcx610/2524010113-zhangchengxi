# Git 学习文档

---

## 一、本地仓库基础操作

### 1. 创建版本库
```
mkdir learngit       # 创建工作目录
git init             # 初始化 Git 仓库
```
>`git init` 会在当前目录生成一个隐藏的 `.git` 文件夹，里面存放了所有的版本历史和配置信息。只要这个文件夹在，你的版本记录就在。

### 2. 提交文件到版本库
```
git add <file>              # 将文件添加到暂存区
git commit -m "提交说明"     # 将暂存区内容提交到分支
```
> `add` + `commit` 是 Git 最核心的两步操作。可以把 `add` 理解为"放入购物车"，`commit` 理解为"下单付款"，每一次 commit 都是一次完整的版本快照。

### 3. 查看提交历史
```
git log                     # 显示从最近到最远的提交日志
git log --pretty=oneline    # 每条日志压缩为一行，简洁展示
git reflog                  # 记录每一次命令操作（包括回退）
```
> `git log` 只能看到当前分支的提交记录，而 `git reflog` 是"后悔药"——哪怕你做了 `reset` 回退，它也能帮你找到之前的 commit id，从而恢复丢失的提交。

---

## 二、版本回退与撤销修改

### 1. 版本回退
```
git reset --hard <commit_id>   # 回退到指定版本（已提交状态）
```
> `--hard` 意味着"彻底回退"，工作区和暂存区都会被覆盖。如果只想回退提交记录但保留代码改动，可以用 `--soft` 或 `--mixed`。

### 2. 撤销修改
```
git checkout -- <file>    # 丢弃工作区的修改
```
> 这个命令的本质是用暂存区或版本库中的版本**覆盖**工作区的文件。注意 `--` 不能省略，否则会变成"切换分支"操作。

---

## 三、工作区与暂存区

> **核心概念**：
> - **工作区（Working Directory）**：你电脑里能看到的目录
> - **暂存区（Stage / Index）**：`.git` 目录下的一个文件，存放即将提交的内容
> - **版本库（Repository）**：`.git` 目录本身，存放所有提交记录

```
git add <file>     # 将修改从工作区放入暂存区
git commit         # 将暂存区的所有修改一次性提交到分支
```

> 每次修改后，如果不用 `git add` 放入暂存区，就不会被包含在 `commit` 中。这个"两步提交"机制是 Git 和其他版本控制系统最大的不同之一，它让你可以在提交前自由地整理和挑选改动。

---

## 四、删除文件

```
rm <file>                    # 先在工作区删除文件
git rm <file>                # 再从版本库中删除该文件
git commit -m "删除文件"      # 提交删除操作
```
> 如果误删了文件，可以用 `git checkout -- <file>` 从版本库中恢复最近一次提交的版本。

---

## 五、远程仓库

### 1. 关联远程库
```
git remote add origin git@server-name:path/repo-name.git
```
> 关联一个远程库时必须给远程库指定一个名字，`origin` 是默认习惯命名。

### 2. 首次推送
```
git push -u origin master    # 第一次推送 master 分支的所有内容
```
> `-u` 参数会把本地的 `master` 分支和远程的 `master` 分支关联起来，此后只需要 `git push` 即可。

### 3. 日常推送
```
git push origin master        # 每次本地提交后，推送最新修改
```

### 4. 克隆仓库
```bash
git clone <repository-url>    # 克隆一个远程仓库到本地
```
> 克隆时 Git 会自动将远程库命名为 `origin`，并自动关联 `main` 或 `master` 分支，比手动关联方便得多。

---

## 六、分支管理

### 1. 分支基本操作
```
git branch                    # 查看分支
git branch <name>             # 创建分支
git checkout <name>           # 切换分支（旧写法）
git switch <name>             # 切换分支（新写法，推荐）
git checkout -b <name>        # 创建 + 切换分支（旧写法）
git switch -c <name>          # 创建 + 切换分支（新写法，推荐）
git merge <name>              # 将指定分支合并到当前分支
git branch -d <name>          # 删除已合并的分支
git branch -D <name>          # 强行删除未合并的分支
```
> `switch` 是 Git 后来新增的命令，专门用来切换分支，比 `checkout` 语义更清晰。`checkout` 既能切换分支又能撤销修改，容易让人混淆。

### 2. 解决合并冲突
> 当 Git 无法自动合并分支时，必须**手动解决冲突**，编辑文件为期望的内容后再提交，合并才算完成。

> 冲突并不可怕，它说明两个分支修改了同一段代码。打开冲突文件，找到 `<<<<<<<`、`=======`、`>>>>>>>` 标记的区域，手动选择保留哪一部分即可。

### 3. Bug 修复工作流
```
git stash              # 把当前工作现场"储藏"起来
# ... 去修复 bug ...
git stash pop          # 修复完成后，恢复工作现场
```
> 在 `master` 分支上修复的 bug，想合并到当前 `dev` 分支，可以用：
> ```bash
> git cherry-pick <commit>    # 把 bug 提交的修改"复制"到当前分支
> ```

> `stash` 就像一个"临时抽屉"，把手头没做完的工作存起来，等紧急任务处理完再拿出来继续。比直接 commit 一个半成品要优雅得多。

---

## 七、远程协作

```
git remote -v                                                # 查看远程库信息
git push origin <branch-name>                                # 从本地推送分支
git pull                                                     # 从远程抓取分支（有冲突先解决）
git checkout -b <branch-name> origin/<branch-name>           # 在本地创建与远程对应的分支
git branch --set-upstream <branch-name> origin/<branch-name> # 建立本地与远程分支的关联
```


> - 本地新建的分支如果不推送到远程，对其他人就是不可见的。
> - 推送失败时，通常是因为远程有新提交，先用 `git pull` 拉取并合并，再重新推送。
> - 本地和远程分支名称最好保持一致，减少认知负担。

---

## 八、提交历史整理

```
git rebase                   # 将本地未 push 的分叉提交历史整理成直线
```
> `rebase` 会把你的提交"重新播放"到目标分支的最新提交之后，使提交历史变成一条干净的线。但**不要对已经推送到远程的提交做 rebase**，否则会给协作者带来混乱。

---

## 九、标签管理

### 1. 创建标签
```
git tag <tagname>                    # 在 HEAD 上新建标签
git tag <tagname> <commit_id>        # 在指定 commit 上新建标签
git tag -a <tagname> -m "说明信息"    # 创建带注释的标签
git tag                              # 查看所有标签
```

### 2. 推送标签
```
git push origin <tagname>        # 推送一个本地标签
git push origin --tags          # 推送全部未推送过的本地标签
```

### 3. 删除标签
```
git tag -d <tagname>                            # 删除本地标签
git push origin :refs/tags/<tagname>            # 删除远程标签
```

> 标签本质是指向某个 commit 的**不可变指针**，通常用于标记发布版本（如 `v1.0`、`v2.1`）。相比 commit id 的一长串哈希值，标签名更直观、更易记。

---

## 十、.gitignore 忽略文件

> 忽略某些文件时，需要编写 `.gitignore` 文件。`.gitignore` 文件本身要放到版本库里，并且可以对 `.gitignore` 做版本管理。

>常见的忽略对象包括编译产物（如 `.o`、`.exe`）、依赖目录（如 `node_modules/`）、IDE 配置文件（如 `.vscode/`）以及包含敏感信息的配置文件。GitHub 上提供了各种语言的 `.gitignore` 模板，可以直接参考使用。

---

> **总结**：Git 的核心思想就是 **"工作区 → 暂存区 → 版本库"** 的三层结构和 **"分支 + 合并"** 的协作模式。掌握了这两条主线，再配合 `stash`、`cherry-pick`、`rebase` 等高级工具，就能应对绝大多数日常开发场景。
