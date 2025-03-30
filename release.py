import argparse
import os
import shutil
import subprocess
import sys

from twine.commands.upload import upload
from twine.settings import Settings


def parse_arguments():
    """解析命令行参数并提供默认值。"""
    parser = argparse.ArgumentParser(description="Automate version bumping and package release.")

    parser.add_argument(
        '--version_part',
        choices=['major', 'minor', 'patch'],
        default='patch',  # 默认值为 'patch'
        help="Version part to bump. Must be one of: major, minor, patch. Default is 'patch'."
    )
    parser.add_argument(
        '--upload',
        action='store_true',
        default=True,  # 默认值为 True
        help="Upload the package to PyPI after building."
    )

    return parser.parse_args()


def bump_version(part):
    """使用 bumpversion 递增版本号。"""
    try:
        subprocess.run(['bumpversion', part], check=True)
        print(f"Version bumped successfully to new {part}.")
    except subprocess.CalledProcessError as e:
        print("Error bumping version:", e)
        sys.exit(1)


def build_package():
    """使用 setuptools 打包项目。"""
    try:
        subprocess.run(['python', 'setup.py', 'sdist', 'bdist_wheel'], check=True)
        print("Package built successfully.")
    except subprocess.CalledProcessError as e:
        print("Error building package:", e)
        sys.exit(1)


def upload_package():
    """使用 twine 上传包到 PyPI。"""
    try:
        subprocess.run(['twine', 'upload', 'dist/*'], check=True)
        print("Package uploaded successfully.")
    except subprocess.CalledProcessError as e:
        print("Error uploading package:", e)
        sys.exit(1)


def clean_dist_directory():
    """Clean the dist directory before building the package."""
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)

def generate_init_files(directory):
    """
    递归地为指定目录及其子目录生成 __init__.py 文件，并使用相对路径自动导入所有子模块。

    :param directory: 要处理的根目录
    """
    for root, dirs, files in os.walk(directory):
        init_file_path = os.path.join(root, '__init__.py')
        relative_path = os.path.relpath(root, directory).replace(os.sep, '.')
        if relative_path == '.':
            relative_path = ''
        else:
            relative_path = '.' + relative_path

        module_names = []
        for file in files:
            if file.endswith('.py') and file != '__init__.py' and not file.startswith('test_'):
                module_name = os.path.splitext(file)[0]
                module_names.append(module_name)


        init_content = ""
        for module_name in module_names:
            import_path = f"from {directory}{relative_path}.{module_name} import *\n"
            init_content += import_path

        for d in dirs:
            if d.startswith('_') or d.startswith('test_'):
                continue
            import_path = f"from {directory}{relative_path}.{d} import *\n"
            init_content += import_path

        with open(init_file_path, 'w', encoding='utf-8') as init_file:
            init_file.write(init_content)


def main():
    args = parse_arguments()

    clean_dist_directory()
    
    target_directory = 'auto_easy'
    generate_init_files(target_directory)

    bump_version(args.version_part)
    build_package()


    if args.upload:
        upload_package()


if __name__ == "__main__":
    main()

