
import pkgutil
import importlib

class ModelLoader:
    def __init__(self, package_name: str):
        self.package_name = package_name

    def load_models(self):
        package = importlib.import_module(self.package_name)
        package_path = package.__path__[0]

        for _, module_name, _ in pkgutil.iter_modules([package_path]):
            importlib.import_module(f"{self.package_name}.{module_name}")