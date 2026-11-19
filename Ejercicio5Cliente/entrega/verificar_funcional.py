from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).parent / "parte2" / "verificar_funcional.py"), run_name="__main__")
