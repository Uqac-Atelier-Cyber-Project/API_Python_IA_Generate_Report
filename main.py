import re
import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from fastapi import FastAPI
from pydantic import BaseModel
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# Create a pool of workers to handle multiple requests in parallel
executor = ProcessPoolExecutor(max_workers=4)

def process_request(prompt):
    """ Function executed in a separate process """
    logger.info("Processing request in a separate process")
    response = ollama.chat(model="deepseek-r1:14b", messages=[{"role": "user", "content": prompt}])
    cleaned_response = re.sub(r'<think>.*?</think>', '', response['message']['content'], flags=re.DOTALL)
    logger.info("Finished processing request")
    return cleaned_response

@app.post("/generate")
async def generate_text(request: PromptRequest):
    try:
        logger.info("Received request with prompt: %s", request.prompt)
        prompt = (
            "Bonjour, tu es un un analyste en cybersécurité, on te fournis différents résultat qui proviennent Scan de port/Attack bruteforce SSH/Attaque Wifi/d'analyse CVE. L'objectif est de détecter les problemes dans ses données de faire un analyse indiquant si c'est problématique et en présentant une échelle de criticité du probleme détecter. De préférence, il faut présenter cela sous la forme de rapport et au besoin tu peux générer des tableau pour résumer certains éléments. Voici une donnée que tu devra traiter : \n"
            + request.prompt
        )

        loop = asyncio.get_running_loop()
        logger.info("Submitting request to executor")
        cleaned_response = await loop.run_in_executor(executor, process_request, prompt)
        logger.info("Received cleaned response")

        return {"response": cleaned_response}
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server")
    uvicorn.run(app, host="0.0.0.0", port=8087)