import pytest
from app.filters import filter_input, filter_output


# ---------------------------------------------------------------------------
# filter_input — PII masking
# ---------------------------------------------------------------------------

class TestPIIMasking:
    def test_phone_plus7(self):
        text, refusal = filter_input("Мой номер +7 (916) 123-45-67")
        assert "[ТЕЛЕФОН_СКРЫТ]" in text
        assert refusal is None

    def test_phone_8(self):
        text, _ = filter_input("Звоните: 8-800-555-35-35")
        assert "[ТЕЛЕФОН_СКРЫТ]" in text

    def test_passport(self):
        text, _ = filter_input("Паспорт 4516 123456")
        assert "[ПАСПОРТ_СКРЫТ]" in text

    def test_snils(self):
        text, _ = filter_input("СНИЛС 123-456-789 01")
        assert "[СНИЛС_СКРЫТ]" in text

    def test_card(self):
        text, _ = filter_input("Карта 4276 1234 5678 9012")
        assert "[КАРТА_СКРЫТА]" in text

    def test_email(self):
        text, _ = filter_input("Почта user@example.com")
        assert "[EMAIL_СКРЫТ]" in text

    def test_no_pii_unchanged(self):
        query = "Как пополнить кошелёк на Токеоне?"
        text, refusal = filter_input(query)
        assert text == query
        assert refusal is None


# ---------------------------------------------------------------------------
# filter_input — investment refusal
# ---------------------------------------------------------------------------

class TestInvestmentRefusal:
    @pytest.mark.parametrize("query", [
        "Стоит ли мне купить ЦФА прямо сейчас?",
        "Сколько я заработаю если вложу 100 тысяч?",
        "Выгодно ли инвестировать в ЦФА?",
        "Куда лучше вложить деньги?",
        "Надёжен ли этот ЦФА?",
    ])
    def test_investment_query_blocked(self, query):
        _, refusal = filter_input(query)
        assert refusal is not None
        assert len(refusal) > 0

    @pytest.mark.parametrize("query", [
        "Как зарегистрироваться на платформе?",
        "Что такое ЦФА?",
        "Как вывести деньги с кошелька?",
    ])
    def test_safe_query_not_blocked(self, query):
        _, refusal = filter_input(query)
        assert refusal is None


# ---------------------------------------------------------------------------
# filter_output — prohibited phrase replacement
# ---------------------------------------------------------------------------

class TestOutputFilter:
    def test_guaranteed_replaced(self):
        result = filter_output("Доход гарантирован по этому ЦФА.")
        assert "гарантирован" not in result.lower()

    def test_no_risk_replaced(self):
        result = filter_output("Это вложение без риска.")
        assert "без риска" not in result.lower()

    def test_recommend_buy_replaced(self):
        result = filter_output("Рекомендую купить этот ЦФА.")
        assert "рекомендую купить" not in result.lower()

    def test_disclaimer_added_when_needed(self):
        result = filter_output("Доход гарантирован.")
        assert "информационный характер" in result

    def test_clean_output_unchanged(self):
        text = "Для пополнения кошелька перейдите в раздел Кошелёк."
        result = filter_output(text)
        assert result == text
