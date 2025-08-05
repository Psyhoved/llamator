from langchain_openai import ChatOpenAI
import llamator
import os
import dotenv

dotenv.load_dotenv()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_KEY2 = os.getenv('OPENROUTER_API_KEY2')

def check_llm(key: str):
  llm = ChatOpenAI(openai_api_key= key, #'lm-studio' OPENROUTER_API_KEY
                  openai_api_base= "https://openrouter.ai/api/v1", #LOCAL_API_URL "https://openrouter.ai/api/v1",
                  model_name= 'qwen/qwen3-14b:free', #"qwen3-14b" 'qwen/qwen3-14b:free' "qwen/qwen-2.5-coder-32b-instruct:free",
                  max_tokens=30000,
                  temperature=0.01)
  return llm.invoke('hi! What model are you?')

key_list = [OPENROUTER_API_KEY, OPENROUTER_API_KEY2]
for key in key_list:
  print(check_llm(key))
