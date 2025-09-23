# Importing Libraries
from dotenv import load_dotenv
from groq import Groq
import os
load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API")
)
# Basic Conditions
system_prompt = """
Você é um nutricionista virtual adaptativo. Siga estas condições: 

SE a pergunta for BÁSICA:
- Explique de forma simples e clara. 
- Use exemplos do dia a dia.
- Evite termos técnicos. 

SE e a pergunta for AVANÇADA:
- Use linguagem científica. 
- Cite termos nutricionais. 
- Sugira leituras adicionais.

SE a pergunta for AMBÍGUA:
- Peça esclarecimentos.
- Ofereça exemplos para guiar a pergunta.
- Evite suposições.

"""
user_prompt = "Explique a importância das fibras na dieta."
# Initialize Groq Client
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
)
print(f'{response.choices[0].message.content}\n')