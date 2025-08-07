#!/usr/bin/env python3
"""
Демонстрационный пример работы MCP + Ollama
Показывает основные возможности без интерактивного ввода
"""

import asyncio
import sys
from ollama_mcp_client import OllamaMCPClient

async def demo():
    """Демонстрация работы MCP с Ollama"""
    print("🚀 Демонстрация MCP + Ollama")
    print("=" * 50)
    
    # Создаем клиент
    client = OllamaMCPClient()
    
    # Запускаем MCP-сервер
    print("📡 Запускаю MCP-сервер...")
    server_process = await client.start_mcp_server()
    
    if not server_process:
        print("❌ Не удалось запустить MCP-сервер")
        return
    
    print("✅ MCP-сервер запущен")
    print(f"🔧 Доступные инструменты: {[tool.name for tool in client.available_tools]}")
    
    # Демонстрационные команды
    demo_commands = [
        "покажи содержимое текущей директории",
        "создай файл demo.txt с текстом 'Привет из MCP!'",
        "прочитай файл demo.txt",
        "покажи информацию о файле demo.txt"
    ]
    
    try:
        for i, command in enumerate(demo_commands, 1):
            print(f"\n📝 Демо {i}: {command}")
            print("🤖 Обрабатываю...")
            
            response = await client.chat_with_tools(command)
            print(f"💬 Ответ: {response}")
            
            if i < len(demo_commands):
                print("\n" + "-" * 30)
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        # Очистка
        print("\n🧹 Завершение демонстрации...")
        if client.mcp_session:
            await client.mcp_session.close()
        
        if server_process:
            server_process.terminate()
            server_process.wait()
        
        print("✅ Демонстрация завершена!")

if __name__ == "__main__":
    asyncio.run(demo())