import re
import asyncio
from concurrent.futures import ProcessPoolExecutor
from fastapi import FastAPI
from pydantic import BaseModel
import ollama

app = FastAPI()


class PromptRequest(BaseModel):
    prompt: str


# Création d'un pool de workers pour traiter plusieurs requêtes en parallèle
executor = ProcessPoolExecutor(max_workers=4)


def process_request(prompt):
    """ Fonction exécutée dans un process séparé """
    response = ollama.chat(model="deepseek-r1:14b", messages=[{"role": "user", "content": prompt}])
    return re.sub(r'<think>.*?</think>', '', response['message']['content'], flags=re.DOTALL)


@app.post("/generate")
async def generate_text(request: PromptRequest):
    prompt = (
            "Bonjour, tu es un un analyste en cybersécurité, on te fournis différents résultat qui proviennent Scan de port/Attack bruteforce SSH/Attaque Wifi/d'analyse CVE. L'objectif est de détecter les problemes dans ses données de faire un analyse indiquant si c'est problématique et en présentant une échelle de criticité du probleme détecter. Voici une donnée que tu devra traiter : \n"
            + request.prompt
    )

    loop = asyncio.get_running_loop()
    cleaned_response = await loop.run_in_executor(executor, process_request, prompt)

    return {"response": cleaned_response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8087)
