#!/usr/bin/env python3
"""
Простой скрипт для запуска демонстрации MCP с Ollama
"""

import subprocess
import sys
import time

def check_ollama():
    """Проверяет, запущен ли Ollama"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def install_dependencies():
    """Устанавливает зависимости"""
    print("📦 Устанавливаю зависимости...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    print("🚀 MCP + Ollama Demo")
    print("=" * 50)
    
    # Проверяем Ollama
    if not check_ollama():
        print("❌ Ollama не запущен!")
        print("Запустите Ollama командой: ollama serve")
        print("И убедитесь, что у вас установлена модель llama3.2: ollama pull llama3.2")
        return
    
    print("✅ Ollama работает")
    
    # Устанавливаем зависимости
    install_dependencies()
    
    # Запускаем клиент
    print("\n🤖 Запускаю MCP клиент...")
    subprocess.run([sys.executable, "ollama_mcp_client.py"])

if __name__ == "__main__":
    main()