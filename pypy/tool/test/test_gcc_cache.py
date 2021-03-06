
from pypy.tool.gcc_cache import *
from pypy.tool.udir import udir
import md5
from pypy.translator.tool.cbuild import ExternalCompilationInfo

def test_gcc_exec():
    f = udir.join("x.c")
    f.write("""
    #include <stdio.h>
    #include <test_gcc_exec.h>
    int main()
    {
       printf("%d\\n", ANSWER);
       return 0;
    }
    """)
    dir1 = udir.join('test_gcc_exec_dir1').ensure(dir=1)
    dir2 = udir.join('test_gcc_exec_dir2').ensure(dir=1)
    dir1.join('test_gcc_exec.h').write('#define ANSWER 3\n')
    dir2.join('test_gcc_exec.h').write('#define ANSWER 42\n')
    eci = ExternalCompilationInfo(include_dirs=[str(dir1)])
    # remove cache
    path = cache_file_path([f], eci, 'build_executable_cache')
    if path.check():
        path.remove()
    assert build_executable_cache([f], eci) == "3\n"
    assert build_executable_cache([f], eci) == "3\n"
    eci2 = ExternalCompilationInfo(include_dirs=[str(dir2)])
    assert build_executable_cache([f], eci2) == "42\n"

def test_gcc_ask():
    f = udir.join("y.c")
    f.write("""
    #include <stdio.h>
    #include <test_gcc_ask.h>
    int main()
    {
       printf("hello\\n");
       return 0;
    }
    """)
    dir1 = udir.join('test_gcc_ask_dir1').ensure(dir=1)
    dir2 = udir.join('test_gcc_ask_dir2').ensure(dir=1)
    dir1.join('test_gcc_ask.h').write('/* hello world */\n')
    dir2.join('test_gcc_ask.h').write('#error boom\n')
    eci = ExternalCompilationInfo(include_dirs=[str(dir1)])
    # remove cache
    path = cache_file_path([f], eci, 'try_compile_cache')
    if path.check():
        path.remove()
    assert try_compile_cache([f], eci)
    assert try_compile_cache([f], eci)
    assert build_executable_cache([f], eci) == "hello\n"
    eci2 = ExternalCompilationInfo(include_dirs=[str(dir2)])
    assert not try_compile_cache([f], eci2)
