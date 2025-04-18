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
    cleaned_response = re.sub(r'```(?:markdown)?\n?(.*?)```', r'\1', response, flags=re.DOTALL)
    logger.info("Finished processing request")
    return cleaned_response


@app.post("/generate")
async def generate_text(request: PromptRequest):
    try:
        logger.debug("Received request with prompt: %s", request.prompt)
        prompt = (
                """
                Tu es un analyste en cybersécurité. Tu reçois des résultats issus de plusieurs modules d’analyse de sécurité automatisés. Ces modules peuvent inclure :
    
    - Scan de ports
    - Tentatives de bruteforce SSH
    - Tentatives de bruteforce WiFi
    - Analyse de vulnérabilités connues (CVE)
    
    Si une de ces analyse n'est pas fait, tu ne dois pas en parler. Tu dis juste qu'aucune analyse n'a été faite.
    
    Ton objectif est de générer un **rapport d’analyse complet en syntaxe Markdown**, permettant de détecter les problèmes potentiels, d’en évaluer la criticité et de formuler des commentaires pertinents.
    
    ## Instructions :
    
    1. Analyse chaque module indépendamment, en créant une section pour chacun :
       - `## Scan de ports` (en traitant l'ensemble des ports ouverts et des services associés, les résultat sont sous forme  de JSON)
       - `## Bruteforce SSH` (Les résultat sont sous forme de JSON)
       - `## Bruteforce WiFi`(Les résultat sont sous forme de JSON, si le json est retourné avec des info et que le psk est rempli c'est que le mot de passe a été trouvé a l'aide d'une attaque de bruteforce ce qui n'est pas bien) 
       - `## Analyse CVE` (les résultat sont fournit sous forme de tableau)
    
    2. Pour chaque section, réalise :
       - Un résumé des éléments détectés
       - Une évaluation de la gravité des problèmes
       - Une **échelle de criticité** (par exemple : Faible, Moyenne, Élevée, Critique)
       - Un ou plusieurs **commentaires d’interprétation** et, si nécessaire, **des recommandations**
    
    3. En fin de rapport, crée un **tableau récapitulatif** synthétique avec les colonnes suivantes :
       - Type d’analyse
       - Problème(s) détecté(s)
       - Niveau de criticité
       - Commentaire ou recommandation
    
    ## Format de sortie :
    Le rapport doit être entièrement rédigé en **Markdown** avec une mise en forme claire, structurée et professionnelle en français. Ne fais pas apparaitre ```markdown ... ``` au début et à la fin du texte renvoyé.
    
    Voici les données à analyser (au format JSON) :
                """
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
