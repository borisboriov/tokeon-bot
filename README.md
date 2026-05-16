# Tokeon Support Bot

RAG-ассистент клиентской поддержки платформы Токеон (ЦФА, группа ПСБ).
Отвечает на вопросы пользователей по базе знаний платформы: инструкции, регламенты, законодательство.

## Стек

- Python 3.13 · LangChain · ChromaDB (локально)
- LLM: GigaChat (основной) · YandexGPT (второй провайдер)
- Embeddings: `intfloat/multilingual-e5-small` (локально, 384 dims)
- UI: Gradio · Config: pydantic-settings + `.env`

## Быстрый старт

```bash
# 1. Клонировать и создать окружение
git clone https://github.com/borisboriov/tokeon-bot.git
cd tokeon-bot
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Конфиг
cp .env.example .env
# Открой .env и заполни GIGACHAT_CREDENTIALS
```

> **База знаний** — нужен симлинк `data/knowledge_base` на директорию с файлами:
> ```bash
> ln -s /path/to/knowledge_base data/knowledge_base
> ```

```bash
# 4. Индексация базы знаний (~13 сек на CPU)
python scripts/ingest.py

# 5. Запуск UI
python main.py
# → http://localhost:7860
```

## Переменные окружения (`.env`)

| Переменная | Описание |
|---|---|
| `LLM_PROVIDER` | `gigachat` или `yandex` |
| `EMBEDDING_PROVIDER` | `local` или `gigachat` |
| `GIGACHAT_CREDENTIALS` | Base64-ключ из личного кабинета Sber Developers |
| `GIGACHAT_SCOPE` | `GIGACHAT_API_PERS` (личный) или `GIGACHAT_API_CORP` |
| `YANDEX_API_KEY` | API-ключ YandexGPT |
| `YANDEX_FOLDER_ID` | ID каталога в Yandex Cloud |
| `TOP_K` | Количество фрагментов для retrieval (по умолчанию 5) |
| `RETRIEVAL_SCORE_THRESHOLD` | Минимальная релевантность (по умолчанию 0.3) |

## Структура проекта

```
app/
  config.py            # pydantic-settings: читает .env
  filters.py           # комплаенс-фильтры: PII, инвест-запросы, выходной фильтр
  prompts.py           # системные промпты по категориям (law / instructions / book)
  rag.py               # RAGPipeline: retrieve + answer
  store.py             # VectorStore: обёртка над ChromaDB
  chunkers/            # разбивка текстов по категориям
    faq.py             #   instructions/ → FAQ / глоссарий / процедуры
    legal.py           #   law/ → по статьям
    book.py            #   book/ + business_requirements/ → по главам
  providers/           # абстракции и реализации LLM/Embeddings
    base.py            #   LLMProvider, EmbeddingProvider (ABC)
    gigachat.py        #   GigaChatLLM, GigaChatEmbeddings
    local.py           #   LocalEmbeddingProvider (sentence-transformers)
    yandex.py          #   YandexLLM, YandexEmbeddings
    factory.py         #   make_llm(), make_embeddings()
data/
  knowledge_base/      # симлинк на KB (не в git)
  chroma/              # векторная БД (не в git)
  golden_set.json      # 30 вопросов с эталонными ответами (10 зел. / 12 жёл. / 8 кр.)
  demo_scenario.md     # сценарий для демонстрации
scripts/
  ingest.py            # индексация: KB → chunks → vectors → ChromaDB
  evaluate.py          # оценка качества: 30 вопросов, LLM-as-judge, отчёт в reports/
  inspect_kb.py        # статистика по базе знаний
  preview_chunks.py    # просмотр чанков по категории
  smoke_providers.py   # проверка LLM + embeddings
  smoke_rag.py         # проверка RAG end-to-end
main.py                # точка входа: запуск Gradio
```

## Комплаенс и безопасность

Бот работает в регуляторном контексте ФЗ-259 (ЦФА) и применяет три уровня защиты:

**Входной фильтр (`filter_input`):**
- Маскирует персональные данные в запросе: телефон, паспорт, СНИЛС, номер карты, email
- Блокирует запросы на инвестиционные рекомендации («стоит ли купить», «сколько заработаю» и др.) и возвращает отказ

**Маршрутизация промптов:**
- Определяет категорию найденных чанков (law / instructions / book)
- Подставляет соответствующий системный промпт с нужным уровнем осторожности

**Выходной фильтр (`filter_output`):**
- Заменяет запрещённые формулировки («гарантировано», «без риска», «рекомендую купить»)
- Добавляет дисклеймер, если ответ касается инвестиционной тематики

## Оценка качества

Golden set: 30 вопросов трёх категорий — зелёная (инструкции), жёлтая (бизнес), красная (отказ от инвест-советов).

```bash
python scripts/evaluate.py
```

Скрипт прогоняет все вопросы через RAG, оценивает ответы через GigaChat (LLM-as-judge) и сохраняет отчёт в `reports/`. Текущий результат: **97% корректного поведения, 3.4/5 качество ответов**.

## Команды разработки

```bash
# Проверить провайдеры (LLM + embeddings)
python scripts/smoke_providers.py

# Проверить RAG end-to-end (3 вопроса)
python scripts/smoke_rag.py

# Полная оценка качества (30 вопросов, ~10 мин)
python scripts/evaluate.py

# Повторная индексация (после изменений в KB)
python scripts/ingest.py

# Статистика по базе знаний
python scripts/inspect_kb.py
```
