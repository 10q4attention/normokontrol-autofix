import os, re
from .base_rule import BaseRule, RuleResult

class FileNamingRule(BaseRule):
    @property
    def rule_id(self): return "file_naming"
    @property
    def name(self): return "Проверка имени файла"
    @property
    def description(self): return "Имя файла должно соответствовать шаблону: 090302_22Т0000_Фамилия"

    def check(self, model):
        fn = model.metadata.get('file_name','')
        fp = model.metadata.get('folder_path','')
        folder_name = os.path.basename(fp)
        folder_surname = folder_name.split('_')[0].split(' ')[0]
        pattern = r'^090302_22[А-Я][0-9]{4}_[А-Яа-яёЁ]+(?:-[А-Яа-яёЁ]+)?\.docx?$'
        exp = '090302_22[БУКВА][4 ЦИФРЫ]_[ФАМИЛИЯ].docx'
        if not re.match(pattern, fn):
            return RuleResult(status='fail', summary='Имя файла не соответствует шаблону',
                details=[f"Имя: '{fn}'", f"Формат: {exp}"],
                received=f"Файл: {fn}", expected=exp)
        file_surname = os.path.splitext(fn)[0].split('_')[-1]
        if folder_surname.lower() != file_surname.lower():
            return RuleResult(status='fail', summary='Фамилия не совпадает с папкой',
                details=[f"Файл: {file_surname}", f"Папка: {folder_surname}"],
                received=f"Файл: {file_surname}", expected=f"Папка: {folder_surname}")
        return RuleResult(status='pass', summary='Имя соответствует требованиям')