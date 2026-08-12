# *Linux*学习文档
一、环境配置
1. 安装 WSL + Ubuntu
2. 安装 VS Code + Remote-WSL
***
二、基础 Shell 指令
1. pwd         # 当前目录
2。 ls          # 列表
3. ls -l       # 详细列表
4. ls -a       # 包含隐藏文件
5. cd          # 切换目录
6. mkdir       # 创建目录
7. touch       # 创建文件
8. cp          # 复制
9. mv          # 移动 / 重命名
10. rm          # 删除
11. cat         # 查看文件
12. echo        # 输出 / 写入
13. wc -l       # 统计行数
14. history     # 历史命令
***
三、文件查找与文本处理
find .                      # 列出所有文件
find . -name "hello.c"      # 按文件名查找
find . -type f              # 只查文件
find . -type d              # 只查目录
grep "printf" hello.c
grep -n "printf" hello.c    # 显示行号
grep -n "main" *.c
cat hello.c | grep "printf"
ls -l | less
grep "printf" *.c | wc -l
***
四、压缩与打包
tar -czvf hello.tar.gz hello.c hello
tar -tzf hello.tar.gz
mkdir extract_test
tar -xzvf hello.tar.gz -C extract_test

zip demo.zip hello.c hello
unzip -l demo.zip
五、权限与用户管理
ls -l
whoami
id
groups
六、进程与资源查看

ps
ps aux | head
top
htop
free -h
df -h
uptime
uname -a
七、环境变量
echo $PATH
which gcc
which code
env
临时：
export MYNAME="zcx"
echo $MYNAME
永久：
echo 'export MYNAME="zcx"' >> ~/.bashrc
source ~/.bashrc
八、远程开发与文件传输
当前已通过 VS Code Remote-WSL 实现远程开发







