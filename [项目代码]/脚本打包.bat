pyinstaller -w -D --clean -i "./Resource/logo.ico" XJ_Main.py
pause

: "默认命令是pyinstaller -F -w ***.py"
: "其他样例命令是pyinstaller -F -w -i Logo.ico Main.py MyLogo.py"
: https://blog.csdn.net/lipenghandsome/article/details/120137667


: --clean: 在构建之前清理PyInstaller缓存并删除临时文件
: -D: 创建包含可执行文件的单文件夹包，同时会有一大堆依赖的 dll 文件，这是默认选项
: -F: 只生成一个 .exe 文件，如果项目比较小的话可以用这个，但比较大的话就不推荐
: -w:不要console(取消类似于cmd的黑框框)
: -i:后面接图标地址（图标一定要是标准的ico格式）
