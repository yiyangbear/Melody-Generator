import sys
import os


def setup_environment():
    """Set up Python path and environment"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import PyQt5
        import mido
        return True
    except ImportError as e:
        print(f"Dependency check failed: {e}")
        return False


def main():
    """Main application entry point"""
    setup_environment()
    
    if not check_dependencies():
        print("Please install missing dependencies:")
        print("pip install PyQt5 mido")
        input("Press Enter to exit...")
        return
    
    try:
        from gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Application runtime error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()