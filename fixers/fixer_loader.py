import os, sys, importlib, inspect
from typing import List
from fixers.base_fixer import BaseFixer


class FixerLoader:
    def __init__(self, fixers_dir: str = 'fixers'):
        self.fixers_dir = fixers_dir
        self.fixers: List[BaseFixer] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.fixers_dir):
            return
        root = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.dirname(root)
        if parent not in sys.path:
            sys.path.insert(0, parent)
        for fn in sorted(os.listdir(self.fixers_dir)):
            if fn.endswith('.py') and not fn.startswith('__') and fn not in ('base_fixer.py', 'fixer_loader.py'):
                mod = fn[:-3]
                try:
                    m = importlib.import_module(f"fixers.{mod}")
                    for name, obj in inspect.getmembers(m):
                        if inspect.isclass(obj) and issubclass(obj, BaseFixer) and obj is not BaseFixer:
                            self.fixers.append(obj())
                except Exception as e:
                    print(f"Ошибка загрузки фиксера {mod}: {e}")

    def get_fixers(self) -> List[BaseFixer]:
        return self.fixers
