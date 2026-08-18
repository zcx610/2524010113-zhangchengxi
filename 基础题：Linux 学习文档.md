# Linux 学习文档

## 一、环境配置

1. 安装 WSL + Ubuntu
2. 安装 VS Code + Remote-WSL

> WSL 相当于在 Windows 里跑了一个真正的 Linux 内核，比传统虚拟机轻量得多，启动快、资源占用小，而且能直接读写 Windows 文件，非常适合日常开发。VS Code 的 Remote-WSL 插件则把编辑器变成了 Linux 环境的"前端"，写代码和调试都在 WSL 里完成，避免了路径和依赖的混乱。

---

## 二、基础 Shell 指令

| 命令 | 说明 |
|------|------|
| `pwd` | 显示当前所在目录（Print Working Directory） |
| `ls` | 列出目录内容 |
| `ls -l` | 以详细列表形式显示（权限、大小、时间等） |
| `ls -a` | 显示所有文件，包括隐藏文件（以 `.` 开头的文件） |
| `cd` | 切换目录（Change Directory） |
| `mkdir` | 创建新目录（Make Directory） |
| `touch` | 创建空文件或更新文件时间戳 |
| `cp` | 复制文件或目录（Copy） |
| `mv` | 移动文件 / 重命名（Move / Rename） |
| `rm` | 删除文件或目录（Remove） |
| `cat` | 查看文件内容（Concatenate） |
| `echo` | 输出字符串或变量值，也可重定向写入文件 |
| `wc -l` | 统计文件行数（Word Count - lines） |
| `history` | 显示历史命令记录 |

> 这些是最常用的"生存命令"。`ls -l` 的输出格式一开始可能觉得复杂，但熟悉后会发现它包含了文件类型、权限、所有者、大小和修改时间等关键信息。`echo` 和 `cat` 虽然简单，但结合重定向和管道能玩出很多花样。

---

## 三、文件查找与文本处理

### 1. find —— 文件查找
```
find .                      # 列出当前目录及子目录下的所有文件
find . -name "hello.c"      # 按文件名精确查找
find . -type f              # 只查找普通文件
find . -type d              # 只查找目录
```

### 2. grep —— 文本搜索
```
grep "printf" hello.c               # 在文件中搜索字符串
grep -n "printf" hello.c            # 显示匹配行及行号
grep -n "main" *.c                  # 在所有 .c 文件中搜索 "main" 并显示行号
```

### 3. 管道组合
```
cat hello.c | grep "printf"         # 将文件内容作为 grep 的输入
ls -l | less                        # 分页查看详细列表
grep "printf" *.c | wc -l           # 统计包含 "printf" 的行数
```

>`find` 和 `grep` 是 Linux 下最强大的两个搜索工具，一个按文件名，一个按内容。管道 `|` 是 Shell 的灵魂，它把多个简单命令串联成一条处理流水线，这种"一个工具只做一件事并做好"的哲学，正是 Unix/Linux 系统的精髓。

---

## 四、压缩与打包

### tar 命令
```
tar -czvf hello.tar.gz hello.c hello   # 打包并 gzip 压缩
tar -tzf hello.tar.gz                  # 查看压缩包内容
mkdir extract_test
tar -xzvf hello.tar.gz -C extract_test # 解压到指定目录
```

### zip 命令
```
zip demo.zip hello.c hello             # 创建 zip 压缩包
unzip -l demo.zip                      # 查看 zip 包内容
```

>Linux 中"打包"和"压缩"是两个概念：`tar` 负责把多个文件打包成一个归档文件，而 `gzip`、`bzip2` 等负责压缩。`tar -czvf` 就是先打包再用 gzip 压缩。zip 格式则同时完成打包和压缩，在跨平台交换文件时更常用。

---

## 五、权限与用户管理

```
ls -l          # 查看文件权限和所有者
whoami         # 显示当前用户名
id             # 显示用户 UID、GID 及所属组
groups         # 显示当前用户所属的所有组
```

> Linux 是一个多用户系统，权限管理是安全的核心。`ls -l` 输出中第一列的 `rwxr-xr--` 分别代表所有者、所属组和其他人的读/写/执行权限。理解这些数字是理解 Linux 安全模型的第一步。

---

## 六、进程与资源查看

```
ps                    # 显示当前终端的进程快照
ps aux | head         # 查看系统所有进程（前几行）
top                   # 动态实时查看进程和资源占用
htop                  # top 的增强版，界面更友好（需安装）
free -h               # 以人类可读格式显示内存使用情况
df -h                 # 以人类可读格式显示磁盘空间
uptime                # 显示系统运行时间和平均负载
uname -a              # 显示全部系统信息（内核、主机名、架构等）
```

> `top` 和 `htop` 是排查系统卡顿的利器，能直观看到哪个进程吃掉了 CPU 或内存。`free -h` 和 `df -h` 中的 `-h` 参数（human-readable）非常实用，它会自动把字节转换成 KB/MB/GB，让数字一目了然。

---

## 七、环境变量

### 查看环境变量
```
echo $PATH      # 显示可执行文件搜索路径
which gcc       # 查找 gcc 命令的位置
which code      # 查找 VS Code 命令的位置
env             # 显示所有环境变量
```

### 临时设置（仅当前会话有效）
```
export MYNAME="zcx"
echo $MYNAME
```

### 永久设置（写入配置文件）
```
echo 'export MYNAME="zcx"' >> ~/.bashrc
source ~/.bashrc   # 重新加载配置使其立即生效
```

>环境变量是进程之间传递配置的重要方式。`PATH` 决定了在终端输入命令时系统去哪些目录查找可执行文件。临时设置用 `export`，永久设置要写入 shell 配置文件（如 `~/.bashrc`），`source` 命令可以免重启立即加载新配置。

---

## 八、远程开发与文件传输

当前已通过 VS Code Remote-WSL 实现远程开发。

>这种方式本质上是让 VS Code 的界面运行在 Windows 上，而代码、终端和所有操作都在 WSL 的 Linux 环境中执行。对于跨平台开发来说，既享受了 Windows 的软件生态，又获得了 Linux 的原生开发体验，是目前最舒适的本地 Linux 开发方案之一。
