import os
import subprocess
import tempfile
import shutil


def create_dmg():
    app_path = "dist/melody_generator.app"
    dmg_name = "Melody Generator_v1.0.dmg"

    if not os.path.exists(app_path):
        print("The application file does not exist. Please build the application first.")
        return

    temp_dir = tempfile.mkdtemp()
    applications_link = os.path.join(temp_dir, "Applications")
    os.symlink("/Applications", applications_link)

    shutil.copytree(app_path, os.path.join(temp_dir, "Melody Generator.app"))

    try:
        subprocess.run([
            "hdiutil", "create",
            "-volname", "Melody Generator",
            "-srcfolder", temp_dir,
            "-ov", dmg_name,
            "-format", "UDZO"
        ], check=True)
        print(f"DMG creation successful: {dmg_name}")
    except subprocess.CalledProcessError as e:
        print(f"DMG creation failed: {e}")
    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    create_dmg()