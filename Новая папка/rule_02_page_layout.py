from .base_rule import BaseRule, RuleResult

class PageLayoutRule(BaseRule):
    @property
    def rule_id(self): return "page_layout"
    @property
    def name(self): return "Параметры страницы"
    @property
    def description(self): return "Проверка полей, ориентации и размера (A4)"

    def check(self, model):
        secs = model.page_setup
        if not secs:
            return RuleResult(status='error', summary='Нет данных о страницах')
        exp = {'top':20,'bottom':20,'left':30,'right':15,'width':210,'height':297}
        errors = []
        for i,s in enumerate(secs,1):
            m = s.get('margins',{})
            if m and not all(v==0 for v in m.values()):
                for side,label in [('top','верхнее'),('bottom','нижнее'),('left','левое'),('right','правое')]:
                    v = m.get(side,0)
                    if abs(v-exp[side])>1.5:
                        errors.append(f"Секция {i}: {label} {v:.1f} мм (должно {exp[side]:.0f})")
            if s.get('orientation')=='landscape':
                errors.append(f"Секция {i}: альбомная (допустимо для широких таблиц)")
            w,h = s.get('width',0), s.get('height',0)
            if w>0 and h>0 and (abs(w-exp['width'])>2 or abs(h-exp['height'])>2):
                errors.append(f"Секция {i}: {w:.0f}x{h:.0f} мм (A4: 210x297)")
        if errors:
            return RuleResult(status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=f"Секций: {len(secs)}", expected="20-20-30-15 мм, A4, книжная")
        return RuleResult(status='pass', summary='Параметры страницы в норме')