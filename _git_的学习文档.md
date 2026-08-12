# *git*的学习文档
一、Markdown 关键知识点总结
1. 创建版本库 mkdir learngit+ git init
2. 提交文件到版本库git add+git commit+-m（提交说明）
3. git log命令显示从最近到最远的提交日志，--pretty=oneline可简化
4. git reflog用来记录你的每一次命令
5. git reset版本回退hard为已提交状态
6. git log命令显示从最近到最远的提交日志
7. git add命令实际上就是把要提交的所有修改放到暂存区（Stage），执行git commit就可以一次性把暂存区的所有修改提交到分支（工作区与暂存区）
8. 每次修改，如果不用git add到暂存区，那就不会加入到commit中
9. git checkout -- file可以丢弃工作区的修改（撤销修改）
10. 先删除文件，再版本库中删除该文件，那就用命令git rm删掉，并且git commit（删除文件）
11. 要关联一个远程库，使用命令git remote add origin git@server-name:path/repo-name.git；
关联一个远程库时必须给远程库指定一个名字，origin是默认习惯命名，关联后，使用命令git push -u origin master第一次推送master分支的所有内容，每次本地提交后，只要有必要，就可以使用命令git push origin master推送最新修改
12. 要克隆一个仓库，首先必须知道仓库的地址，然后使用git clone命令克隆
13. 1.查看分支：git branch
2.创建分支：git branch <name>
3.切换分支：git checkout <name>或者git switch <name>
4.创建+切换分支：git checkout -b <name>或者git switch -c <name>
5.合并某分支到当前分支：git merge <name>
6.删除分支：git branch -d <name>
14. 当Git无法自动合并分支时，就必须首先解决冲突。解决冲突后，再提交，合并完成。
解决冲突就是把Git合并失败的文件手动编辑为我们希望的内容，再提交
15. 通过创建新的bug分支进行修复，然后合并，最后删除；
当手头工作没有完成时，先把工作现场git stash一下，然后去修复bug，修复后，再git stash pop，回到工作现场；在master分支上修复的bug，想要合并到当前dev分支，可以用git cherry-pick <commit>命令，把bug提交的修改“复制”到当前分支
16. 如果要丢弃一个没有被合并过的分支，可以通过git branch -D <name>强行删除
17. 1.查看远程库信息，使用git remote -v；
本地新建的分支如果不推送到远程，对其他人就是不可见的；
2.从本地推送分支，使用git push origin branch-name，如果推送失败，先用git pull抓取远程的新提交；
3.在本地创建和远程分支对应的分支，使用git checkout -b branch-name origin/branch-name，本地和远程分支的名称最好一致；
4.建立本地分支和远程分支的关联，使用git branch --set-upstream branch-name origin/branch-name；
5.从远程抓取分支，使用git pull，如果有冲突，要先处理冲突。
18. rebase操作可以把本地未push的分叉提交历史整理成直线
19. git tag <tagname>用于新建一个标签，默认为HEAD，也可以指定一个commit id 命令git tag -a <tagname> -m "blablabla..."可以指定标签信息；命令git tag可以查看所有标签。
20. git push origin <tagname>可以推送一个本地标签；
命令git push origin --tags可以推送全部未推送过的本地标签；
命令git tag -d <tagname>可以删除一个本地标签；
命令git push origin :refs/tags/<tagname>可以删除一个远程标签
21. 忽略某些文件时，需要编写.gitignore；.gitignore文件本身要放到版本库里，并且可以对.gitignore做版本管理












