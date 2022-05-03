#!/usr/bin/env python3

from datetime import datetime
import json
import stat
import os
import openai
import hashlib
from dotenv import load_dotenv

SCRIPT_DIR = os.path.realpath(__file__).replace('/pythia.py', '')
load_dotenv(f"{SCRIPT_DIR}/.env")
CACHE_PATH = f"{SCRIPT_DIR}/cache.json"
STOP_STR = "|END|"

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

if OPEN_AI_API_KEY is None:
  print("Expected .env variable called OPEN_AI_API_KEY, see https://beta.openai.com/account/api-keys")
  exit(1)

openai.api_key = os.getenv("OPEN_AI_API_KEY")

def cacheInit():
  if not os.path.isfile(CACHE_PATH):
    with open(CACHE_PATH, 'w') as file_object:
      file_object.write("{}")
      file_object.close()

def cacheGet(key):
  cacheInit()

  with open(CACHE_PATH) as file_object:
    cache = json.load(file_object)
    try:
      value = cache[key]
      return value
    except:
      print(f"Could not find '{key}' in cache")
  
  return None

def cacheSet(key, value):
  cacheInit()

  with open(CACHE_PATH) as file_object:
    cache = json.load(file_object)
    file_object.close()

  with open(CACHE_PATH, "w") as file_object:
    cache[key] = value
    json.dump(cache, file_object)
  
  return True

def createScript(input_prompt_md5, input_prompt):
  response = openai.Completion.create(
    engine="text-davinci-002",
    prompt=input_prompt,
    temperature=0,
    max_tokens=100,
    top_p=1,
    frequency_penalty=0.2,
    presence_penalty=0,
    stop=[STOP_STR]
  )

  try:
    firstChoice = response.choices[0]
  except:
    print("The AI is not smart enought to code that!")
    return None

  text = f"""#!/usr/bin/env python3
{firstChoice.text}
"""

  script_id = datetime.now().strftime("%Y%m%d_%H%M%S")
  script_path = f"{SCRIPT_DIR}/scripts/script-{script_id}.py"
  file_object = open(script_path, "w")
  file_object.write(text)
  file_object.close()
  os.chmod(script_path, stat.S_IRWXU)

  cacheSet(input_prompt_md5, script_path)

  return script_path

def createOrGetScript(input_prompt):
  input_prompt_md5 = hashlib.md5(input_prompt.encode()).hexdigest()

  script_path = cacheGet(input_prompt_md5)

  if script_path is not None:
    print(f"Found in cache: {input_prompt_md5}")

    if os.path.isfile(script_path):
      return script_path
    else:
      print("Cached script is missing")

  return createScript(input_prompt_md5, input_prompt)

input_command = input("Instructions: ")

input_prompt = f"""Convert this text to python:
{input_command}
{STOP_STR}"""

script_path = createOrGetScript(input_prompt)

if script_path is None:
  print(f"Something went wrong!")

answer = input("Do you want to execute the script? ") 
if answer[0].lower() == "y":
  os.system(f"python3 {script_path}")

answer = input("Do you want to open the script? ") 
if answer[0].lower() == "y":
  os.system(f"code {script_path}")