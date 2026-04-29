import os, sys, importlib, inspect
from typing import List
from rules.base_rule import BaseRule


class RuleLoader:
    def __init__(self, rules_dir: str = 'rules'):
        self.rules_dir = rules_dir
        self.rules: List[BaseRule] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.rules_dir):
            return
        root = os.path.dirname(os.path.abspath(__file__))
        if root not in sys.path:
            sys.path.insert(0, root)
        for fn in sorted(os.listdir(self.rules_dir)):
            if fn.endswith('.py') and not fn.startswith('__') and fn not in ('base_rule.py', 'document_loader.py'):
                mod = fn[:-3]
                try:
                    m = importlib.import_module(f"rules.{mod}")
                    for name, obj in inspect.getmembers(m):
                        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj is not BaseRule:
                            self.rules.append(obj())
                except Exception as e:
                    print(f"Ошибка загрузки {mod}: {e}")

    def reload(self):
        self.rules.clear()
        for m in list(sys.modules):
            if m.startswith('rules.') and m not in ('rules.base_rule', 'rules.document_loader'):
                del sys.modules[m]
        self._load()

    def get_rules(self) -> List[BaseRule]:
        return self.rules