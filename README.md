# MCP + Ollama: Простой пример интеграции

Этот проект демонстрирует, как работает **MCP (Model Context Protocol)** и как подключить локальную LLM (Ollama) к MCP-серверу с инструментами.

## Что такое MCP?

**Model Context Protocol (MCP)** — это открытый протокол, разработанный Anthropic, который позволяет LLM-моделям безопасно подключаться к внешним источникам данных и инструментам.

### Ключевые концепции MCP:

1. **Сервер (MCP Server)** — предоставляет инструменты и ресурсы
2. **Клиент (MCP Client)** — использует инструменты (обычно интегрирован с LLM)
3. **Инструменты (Tools)** — функции, которые LLM может вызывать
4. **Ресурсы (Resources)** — данные, к которым LLM может получить доступ

### Архитектура:

```
┌─────────────┐    MCP Protocol    ┌─────────────┐
│   LLM       │ ←────────────────→ │ MCP Server  │
│  (Ollama)   │     JSON-RPC       │             │
└─────────────┘                    └─────────────┘
                                           │
                                           ▼
                                   ┌─────────────┐
                                   │  Tools &    │
                                   │  Resources  │
                                   └─────────────┘
```

## Файлы проекта

- `mcp_server.py` — MCP-сервер с инструментами для работы с файлами
- `ollama_mcp_client.py` — клиент для подключения Ollama к MCP-серверу
- `run_demo.py` — простой скрипт для запуска демонстрации
- `requirements.txt` — зависимости проекта

## Как работает наш пример

### 1. MCP-сервер (`mcp_server.py`)

Сервер предоставляет 4 инструмента:

- **`read_file`** — чтение файла
- **`write_file`** — запись в файл
- **`list_directory`** — просмотр содержимого директории
- **`get_file_info`** — информация о файле

#### Структура MCP-сервера:

```python
# 1. Создание сервера
server = Server("file-operations-server")

# 2. Регистрация инструментов
@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [Tool(...), Tool(...)]

# 3. Обработка вызовов инструментов
@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict) -> List[TextContent]:
    # Логика выполнения инструментов
```

### 2. MCP-клиент (`ollama_mcp_client.py`)

Клиент:
1. Запускает MCP-сервер как subprocess
2. Подключается к серверу через stdio
3. Получает список доступных инструментов
4. Интегрирует их с Ollama

#### Поток работы:

```python
# 1. Инициализация MCP-сессии
session = ClientSession(read_stream, write_stream)
await session.initialize(InitializeRequest(...))

# 2. Получение инструментов
tools = await session.list_tools()

# 3. Вызов инструмента
result = await session.call_tool(tool_name, arguments)
```

### 3. Интеграция с Ollama

Поскольку Ollama пока не поддерживает MCP нативно, мы используем промпт-инжиниринг:

1. **Описываем инструменты** в системном промпте
2. **Парсим ответ** LLM на предмет вызовов инструментов
3. **Выполняем инструменты** через MCP
4. **Возвращаем результат** пользователю

```python
# Промпт с описанием инструментов
system_prompt = f"""
Ты ассистент с доступом к следующим инструментам:
{tools_description}

Если нужно использовать инструмент, ответь в формате:
TOOL_CALL: {{"name": "tool_name", "arguments": {...}}}
"""

# Парсинг ответа и выполнение инструмента
if "TOOL_CALL:" in response:
    tool_call = json.loads(response_part)
    result = await execute_tool(tool_call["name"], tool_call["arguments"])
```

## Запуск проекта

### Предварительные требования:

1. **Установите Ollama**: https://ollama.ai/
2. **Запустите Ollama**: `ollama serve`
3. **Скачайте модель**: `ollama pull llama3.2`

### Запуск:

```bash
# Способ 1: Через скрипт запуска
python run_demo.py

# Способ 2: Напрямую
pip install -r requirements.txt
python ollama_mcp_client.py
```

## Примеры использования

После запуска попробуйте эти команды:

```
👤 Вы: покажи содержимое текущей директории
🤖 Ассистент: [выполняет list_directory и показывает файлы]

👤 Вы: создай файл hello.txt с текстом "Привет, MCP!"
🤖 Ассистент: [выполняет write_file]

👤 Вы: прочитай файл hello.txt
🤖 Ассистент: [выполняет read_file и показывает содержимое]

👤 Вы: покажи информацию о файле hello.txt
🤖 Ассистент: [выполняет get_file_info и показывает размер, дату изменения]
```

## Протокол MCP в деталях

### Инициализация соединения:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "ollama-mcp-client",
      "version": "1.0.0"
    }
  }
}
```

### Запрос списка инструментов:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

### Вызов инструмента:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/path/to/file.txt"
    }
  }
}
```

## Преимущества MCP

1. **Безопасность** — контролируемый доступ к ресурсам
2. **Стандартизация** — единый протокол для всех инструментов
3. **Расширяемость** — легко добавлять новые инструменты
4. **Интероперабельность** — работает с разными LLM

## Возможные расширения

1. **Больше инструментов** — HTTP API, базы данных, веб-скрапинг
2. **Authentification** — добавить авторизацию для инструментов
3. **Resources** — помимо tools, добавить ресурсы (документы, изображения)
4. **Streaming** — поддержка потоковых ответов

## Ограничения текущей реализации

1. **Промпт-инжиниринг** вместо нативной поддержки MCP в Ollama
2. **Простой парсинг** JSON из ответа LLM (может быть ненадежным)
3. **Отсутствие error handling** для сложных сценариев

## Полезные ссылки

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

---

**Примечание**: Это демонстрационный пример. Для продакшена потребуются дополнительная обработка ошибок, валидация входных данных и улучшенная безопасность.