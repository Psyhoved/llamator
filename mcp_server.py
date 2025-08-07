#!/usr/bin/env python3
"""
Простой MCP-сервер с функциональностью работы с файлами
Демонстрирует основные концепции MCP-протокола
"""

import json
import os
import sys
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

# Устанавливаем зависимости, если их нет
try:
    from mcp.server.models import InitializeRequest, ServerCapabilities
    from mcp.server.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    print("Устанавливаем зависимости MCP...")
    os.system("pip install mcp")
    from mcp.server.models import InitializeRequest, ServerCapabilities
    from mcp.server.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )

# Создаем экземпляр сервера
server = Server("file-operations-server")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Возвращает список доступных инструментов"""
    return [
        Tool(
            name="read_file",
            description="Читает содержимое файла",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string", 
                        "description": "Путь к файлу"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Записывает содержимое в файл",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу"
                    },
                    "content": {
                        "type": "string",
                        "description": "Содержимое для записи"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="Показывает содержимое директории",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к директории"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="get_file_info",
            description="Получает информацию о файле (размер, дата изменения)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу"
                    }
                },
                "required": ["path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Обрабатывает вызовы инструментов"""
    
    if name == "read_file":
        try:
            path = arguments["path"]
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [TextContent(type="text", text=f"Содержимое файла {path}:\n\n{content}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Ошибка при чтении файла: {str(e)}")]
    
    elif name == "write_file":
        try:
            path = arguments["path"]
            content = arguments["content"]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return [TextContent(type="text", text=f"Файл {path} успешно записан")]
        except Exception as e:
            return [TextContent(type="text", text=f"Ошибка при записи файла: {str(e)}")]
    
    elif name == "list_directory":
        try:
            path = arguments["path"]
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
            
            result = f"Содержимое директории {path}:\n" + "\n".join(items)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Ошибка при просмотре директории: {str(e)}")]
    
    elif name == "get_file_info":
        try:
            path = arguments["path"]
            stat = os.stat(path)
            import datetime
            
            info = f"""Информация о файле {path}:
• Размер: {stat.st_size} bytes
• Дата изменения: {datetime.datetime.fromtimestamp(stat.st_mtime)}
• Права доступа: {oct(stat.st_mode)[-3:]}
• Тип: {'Директория' if os.path.isdir(path) else 'Файл'}"""
            
            return [TextContent(type="text", text=info)]
        except Exception as e:
            return [TextContent(type="text", text=f"Ошибка при получении информации о файле: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"Неизвестный инструмент: {name}")]

async def main():
    # Запускаем сервер через stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializeRequest(
                protocolVersion="2024-11-05",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
                clientInfo={
                    "name": "ollama-mcp-client",
                    "version": "1.0.0",
                },
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())