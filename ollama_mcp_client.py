#!/usr/bin/env python3
"""
Клиент для подключения Ollama к MCP-серверу
Демонстрирует интеграцию локальной LLM с MCP-протоколом
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import requests
    from mcp.client.models import InitializeRequest
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Устанавливаем зависимости...")
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp", "requests"])
    import requests
    from mcp.client.models import InitializeRequest
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client

class OllamaMCPClient:
    def __init__(self, ollama_host: str = "http://localhost:11434", model_name: str = "llama3.2"):
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.mcp_session: Optional[ClientSession] = None
        self.available_tools: List[Dict] = []
        
    async def start_mcp_server(self):
        """Запускает MCP-сервер и устанавливает соединение"""
        try:
            # Запускаем MCP-сервер как subprocess
            server_process = subprocess.Popen(
                [sys.executable, "/workspace/mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Подключаемся к серверу через stdio
            read_stream, write_stream = stdio_client()
            
            self.mcp_session = ClientSession(read_stream, write_stream)
            
            # Инициализируем соединение
            await self.mcp_session.initialize(
                InitializeRequest(
                    protocolVersion="2024-11-05",
                    capabilities={},
                    clientInfo={
                        "name": "ollama-mcp-client", 
                        "version": "1.0.0"
                    }
                )
            )
            
            # Получаем список доступных инструментов
            tools_response = await self.mcp_session.list_tools()
            self.available_tools = tools_response.tools
            
            logger.info(f"Подключение к MCP-серверу установлено. Доступно инструментов: {len(self.available_tools)}")
            return server_process
            
        except Exception as e:
            logger.error(f"Ошибка при подключении к MCP-серверу: {e}")
            return None
    
    def call_ollama(self, prompt: str, tools: List[Dict] = None) -> str:
        """Вызывает Ollama с промптом и инструментами"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            if tools:
                payload["tools"] = tools
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Ошибка Ollama: {response.status_code}"
                
        except Exception as e:
            return f"Ошибка при обращении к Ollama: {e}"
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Выполняет инструмент через MCP"""
        try:
            if not self.mcp_session:
                return "MCP-сессия не инициализирована"
            
            result = await self.mcp_session.call_tool(tool_name, arguments)
            
            if result.content:
                return result.content[0].text if result.content[0].type == "text" else str(result.content[0])
            else:
                return "Инструмент выполнен, но результат пуст"
                
        except Exception as e:
            return f"Ошибка при выполнении инструмента: {e}"
    
    def format_tools_for_ollama(self) -> List[Dict]:
        """Форматирует MCP-инструменты для Ollama"""
        formatted_tools = []
        
        for tool in self.available_tools:
            formatted_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            formatted_tools.append(formatted_tool)
        
        return formatted_tools
    
    async def chat_with_tools(self, user_message: str) -> str:
        """Основной метод для чата с использованием инструментов"""
        
        # Создаем промпт с описанием доступных инструментов
        tools_description = "\n".join([
            f"- {tool.name}: {tool.description}" 
            for tool in self.available_tools
        ])
        
        system_prompt = f"""Ты ассистент с доступом к следующим инструментам:

{tools_description}

Если пользователь просит выполнить операцию, которая требует использования инструментов, 
ответь в формате:
TOOL_CALL: {{
    "name": "имя_инструмента",
    "arguments": {{"параметр": "значение"}}
}}

Если инструменты не нужны, отвечай обычно.

Пользователь: {user_message}
"""

        # Получаем ответ от Ollama
        ollama_response = self.call_ollama(system_prompt)
        
        # Проверяем, хочет ли модель использовать инструмент
        if "TOOL_CALL:" in ollama_response:
            try:
                # Извлекаем вызов инструмента
                tool_call_start = ollama_response.find("TOOL_CALL:") + len("TOOL_CALL:")
                tool_call_json = ollama_response[tool_call_start:].strip()
                
                # Находим JSON-блок
                if tool_call_json.startswith('{'):
                    # Ищем закрывающую скобку
                    bracket_count = 0
                    end_pos = 0
                    for i, char in enumerate(tool_call_json):
                        if char == '{':
                            bracket_count += 1
                        elif char == '}':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_pos = i + 1
                                break
                    
                    tool_call_json = tool_call_json[:end_pos]
                
                tool_call = json.loads(tool_call_json)
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]
                
                # Выполняем инструмент
                tool_result = await self.execute_tool(tool_name, tool_args)
                
                # Формируем финальный ответ
                final_prompt = f"""Пользователь спросил: {user_message}

Я выполнил инструмент {tool_name} с параметрами {tool_args}
Результат: {tool_result}

Дай пользователю понятный ответ на основе этого результата."""

                final_response = self.call_ollama(final_prompt)
                return final_response
                
            except Exception as e:
                return f"Ошибка при обработке вызова инструмента: {e}\n\nОригинальный ответ: {ollama_response}"
        
        return ollama_response

async def main():
    """Главная функция для демонстрации работы"""
    print("🚀 Запуск Ollama MCP Client...")
    
    client = OllamaMCPClient()
    
    # Запускаем MCP-сервер
    server_process = await client.start_mcp_server()
    if not server_process:
        print("❌ Не удалось запустить MCP-сервер")
        return
    
    print("✅ MCP-сервер запущен")
    print(f"📋 Доступные инструменты: {[tool.name for tool in client.available_tools]}")
    
    # Интерактивный чат
    print("\n💬 Интерактивный чат (введите 'quit' для выхода):")
    print("Примеры команд:")
    print("- 'покажи содержимое текущей директории'")
    print("- 'создай файл test.txt с текстом Hello World'")
    print("- 'прочитай файл test.txt'")
    print("- 'покажи информацию о файле test.txt'")
    
    try:
        while True:
            user_input = input("\n👤 Вы: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'выход']:
                break
            
            if not user_input:
                continue
            
            print("🤖 Обрабатываю...")
            response = await client.chat_with_tools(user_input)
            print(f"🤖 Ассистент: {response}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Завершение работы...")
    
    finally:
        # Закрываем MCP-сессию
        if client.mcp_session:
            await client.mcp_session.close()
        
        # Завершаем процесс сервера
        if server_process:
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())