import PyInstaller.__main__
import os
import shutil


def build_mac_app():
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    PyInstaller.__main__.run([
        'src/main.py',
        '--name=melody_generator',
        '--windowed',
        '--icon=resources/icons/app_icon.icns',
        '--add-data=src/generator.py:.',
        '--add-data=src/gui.py:.',
        '--clean',
        '--noconfirm'
    ])

    print("Application packaging completed!")
    print("Application Location: dist/Melody Generator.app")


if __name__ == '__main__':
    build_mac_app()