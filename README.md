# Tokeon Support Bot

RAG-ассистент клиентской поддержки платформы Токеон (ЦФА, группа ПСБ).
Отвечает на вопросы по базе знаний с учётом регуляторных ограничений финтеха.

## Стек

- Python 3.11+
- LangChain + ChromaDB (локально)
- GigaChat (основной LLM + эмбеддинги), YandexGPT (второй провайдер)
- Gradio UI
- pydantic-settings + .env

## Запуск

```bash
# 1. Виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Конфиг
cp .env.example .env
# заполни GIGACHAT_CREDENTIALS в .env

# 4. (потом) Индексация базы знаний
python scripts/ingest.py

# 5. (потом) Запуск UI
python -m app.main
```

## Структура

```
app/         # код приложения
  providers/   # абстракции LLM/Embeddings + реализации (GigaChat, Yandex)
  prompts/     # шаблоны промптов по категориям
data/
  knowledge_base/  # симлинк на базу знаний (не в git)
  chroma/          # локальная векторная БД (не в git)
scripts/     # инспекция базы, индексация, оценка
eval/        # golden set + LLM-as-judge
```

## База знаний

База лежит снаружи репозитория, в `data/knowledge_base` симлинк.
Точка входа — `root.yaml`, который импортирует 4 под-yaml: `book/`, `business_requirements/`, `instructions/`, `law/`.
