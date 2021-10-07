from subprocess import check_output, run, PIPE
import os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def info():
    p = run('python3 setup.py --name', shell=True, stdout=PIPE, check=True)
    name = p.stdout.decode().strip()
    p = run('python3 setup.py --version', shell=True, stdout=PIPE, check=True)
    version = p.stdout.decode().strip()
    check = version.replace('.', '').isdigit()
    assert check, f'v{version} Must be numerical (security check)'
    assert ' ' not in name, f'"{name}" must not have spaces (security check)'
    return name, version


def submit():
    run('rm ./dist/*', shell=True, check=False, stderr=PIPE)
    run('python3 setup.py check', shell=True, check=True)
    run('python3 setup.py sdist', shell=True, check=True)
    run('twine upload dist/*', shell=True, check=True, stdin=sys.stdin)
    return


name, version = info()
print(name, version)

submit()

run('git add .', shell=True, check=True)
run(f'git commit -m "v{version} of {name}"', shell=True, check=True)
run('git push', shell=True, check=True)

run(f'pip3 install --upgrade {name}', shell=True, check=True)
run(f'pip3 install --upgrade {name}', shell=True, check=True)
