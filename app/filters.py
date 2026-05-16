import re

# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------
_PII_PATTERNS = [
    (re.compile(r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'), '[ТЕЛЕФОН_СКРЫТ]'),
    (re.compile(r'\b\d{4}\s\d{6}\b'), '[ПАСПОРТ_СКРЫТ]'),
    (re.compile(r'\b\d{3}-\d{3}-\d{3}\s?\d{2}\b'), '[СНИЛС_СКРЫТ]'),
    (re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'), '[КАРТА_СКРЫТА]'),
    (re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'), '[EMAIL_СКРЫТ]'),
]

# ---------------------------------------------------------------------------
# Investment advisory triggers — requests for personal recommendations
# ---------------------------------------------------------------------------
_INVEST_TRIGGERS = [
    r'стоит\s+ли\s+(\w+\s+)?(купить|вложить|инвестировать)',
    r'надёж\w*\s+ли|надеж\w*\s+ли',
    r'сколько\s+(я\s+)?(заработаю|получу|дохода)',
    r'гарантия\s+прибыли',
    r'(рекомендует|советует)\w*\s+(ли\s+)?(купить|вложить)',
    r'выгодно\s+ли\s+(вкладывать|инвестировать|покупать)',
    r'(стоит|нужно)\s+ли\s+мне\s+(вкладывать|покупать|инвестировать)',
    r'куда\s+(лучше|выгоднее)\s+(вложить|инвестировать)',
    r'(риски?\s+маленьк|безрисков)\w+',
    r'точно\s+заработ\w+',
]
_INVEST_RE = re.compile('|'.join(_INVEST_TRIGGERS), re.IGNORECASE)

_INVEST_REFUSAL = (
    "Платформа Токеон не предоставляет индивидуальных инвестиционных рекомендаций. "
    "Решение о приобретении ЦФА принимается самостоятельно с учётом собственного "
    "риск-профиля. При необходимости проконсультируйтесь с финансовым советником."
)

# ---------------------------------------------------------------------------
# Output prohibited phrases → neutral replacements
# ---------------------------------------------------------------------------
_OUTPUT_REPLACEMENTS = [
    (re.compile(r'гарантиров\w+', re.IGNORECASE), 'предусмотрено'),
    (re.compile(r'без\s+риска', re.IGNORECASE), 'с учётом рисков'),
    (re.compile(r'(рекомендую|советую)\s+(купить|вложить|приобрести)', re.IGNORECASE), 'можно рассмотреть'),
    (re.compile(r'(рекомендуем|советуем)\s+(купить|вложить|приобрести)', re.IGNORECASE), 'можно рассмотреть'),
    (re.compile(r'стоит\s+купить', re.IGNORECASE), 'можно рассмотреть'),
    (re.compile(r'точно\s+заработ\w+', re.IGNORECASE), 'возможен доход'),
    (re.compile(r'выгодное\s+вложение', re.IGNORECASE), 'вложение'),
]

_DISCLAIMER = (
    "\n\n*Данный ответ носит информационный характер и не является "
    "индивидуальной инвестиционной рекомендацией.*"
)

_DISCLAIMER_TRIGGERS = re.compile(
    r'гарантиров|без\s+риска|рекомендую\s+купить|советую\s+купить'
    r'|рекомендуем\s+купить|советуем\s+купить|стоит\s+купить|точно\s+заработ',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_input(text: str) -> tuple[str, str | None]:
    """Return (cleaned_text, refusal) where refusal is set if investment advice requested."""
    if _INVEST_RE.search(text):
        return text, _INVEST_REFUSAL

    cleaned = text
    for pattern, replacement in _PII_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned, None


def filter_output(text: str) -> str:
    """Replace prohibited phrases; append disclaimer if needed."""
    needs_disclaimer = bool(_DISCLAIMER_TRIGGERS.search(text))
    for pattern, replacement in _OUTPUT_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    if needs_disclaimer:
        text += _DISCLAIMER
    return text
