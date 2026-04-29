import re
from .base_rule import BaseRule, RuleResult

class HeadingsLevel2Rule(BaseRule):
    @property
    def rule_id(self): return "headings_level2"
    @property
    def name(self): return "Заголовки второго уровня"
    @property
    def description(self): return "Проверка нумерации подразделов и приложений"

    # Буквы, исключённые для приложений
    FORBIDDEN_APPENDIX = ['Ё', 'З', 'Й', 'О', 'Ч', 'Ь', 'Ы', 'Ъ']

    def check(self, model):
        l1 = [h for h in model.headings if h['level'] == 1]
        l2 = [h for h in model.headings if h['level'] == 2]

        if not l1:
            return RuleResult(status='fail', summary='Нет заголовков 1 уровня')

        errors = []

        for h2 in l2:
            text = h2['text']

            # Проверяем цифровой формат X.Y
            n = re.match(r'^(\d+)\.(\d+)\b', text)
            if n:
                sn, sub = n.group(1), n.group(2)

                # Принадлежность разделу
                parent = None
                for h in l1:
                    m = re.match(r'^(\d+)\b', h['text'])
                    if m and m.group(1) == sn:
                        parent = h
                        break

                if not parent:
                    errors.append(f"'{text[:60]}': не найден раздел {sn}")
                else:
                    # Последовательность внутри раздела
                    siblings = []
                    for h in l2:
                        m = re.match(rf'^{sn}\.(\d+)\b', h['text'])
                        if m:
                            siblings.append((int(m.group(1)), h))
                    siblings.sort(key=lambda x: x[0])
                    pos = next(i for i, s in enumerate(siblings) if s[1] is h2)
                    if pos > 0:
                        prev = siblings[pos - 1][0]
                        curr = int(sub)
                        if curr != prev + 1:
                            errors.append(f"Нарушение нумерации: после {sn}.{prev} идёт {sn}.{curr}")

            # Проверяем формат Приложения
            elif app := re.match(r'^Приложение\s+([А-ЯA-Z])\b', text, re.I):
                letter = app.group(1).upper()

                # Запрещённые буквы
                if letter in self.FORBIDDEN_APPENDIX:
                    errors.append(f"'{text[:60]}': буква '{letter}' не используется для приложений")

                # Последовательность приложений
                all_apps = []
                for h in l2:
                    am = re.match(r'^Приложение\s+([А-ЯA-Z])\b', h['text'], re.I)
                    if am:
                        all_apps.append((am.group(1).upper(), h))

                # Проверяем порядок
                valid_letters = [l for l in 'АБВГДЕЖИКЛМНПРСТУФХЦЧШЩЭЮЯ' if l not in self.FORBIDDEN_APPENDIX]
                found_letters = sorted(set(a[0] for a in all_apps),
                                       key=lambda x: valid_letters.index(x) if x in valid_letters else 999)

                if len(found_letters) > 1:
                    pos = found_letters.index(letter) if letter in found_letters else -1
                    if pos > 0:
                        prev_letter = found_letters[pos - 1]
                        # Проверяем, что буквы идут подряд по алфавиту
                        prev_idx = valid_letters.index(prev_letter) if prev_letter in valid_letters else -1
                        curr_idx = valid_letters.index(letter) if letter in valid_letters else -1
                        if curr_idx != prev_idx + 1:
                            errors.append(f"Нарушение порядка приложений: после {prev_letter} идёт {letter}")

            else:
                # Не подходит ни под X.Y, ни под Приложение
                if not re.match(r'^\d+\.\d+', text) and not re.match(r'^Приложение\s+[А-ЯA-Z]', text, re.I):
                    errors.append(f"Неверный формат: '{text[:60]}' (ожидается X.Y или Приложение А)")

        if errors:
            return RuleResult(status='fail', summary=f'Ошибок: {len(errors)}', details=errors,
                received=f"Подразделов: {len(l2)}",
                expected="Формат X.Y, последовательная нумерация. Приложения: А, Б, В... (без Ё,З,Й,О,Ч,Ь,Ы,Ъ)")

        if not l2:
            return RuleResult(status='pass', summary='Подразделы отсутствуют')

        return RuleResult(status='pass', summary=f'Все {len(l2)} подразделов верны')