import os
import shutil
import PyInstaller.__main__


def build_windows_app():
    """Build the Windows executable with PyInstaller."""

    print("Cleaning previous build files...")

    if os.path.exists("build"):
        shutil.rmtree("build")

    if os.path.exists("dist"):
        shutil.rmtree("dist")

    print("Building Melody Generator for Windows...")

    PyInstaller.__main__.run([
        "src/main.py",
        "--name=MelodyGenerator",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
    ])

    print()
    print("Build completed successfully.")
    print("Executable: dist/MelodyGenerator.exe")


if __name__ == "__main__":
    build_windows_app()