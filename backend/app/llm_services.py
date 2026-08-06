import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_answer(question: str, context: str):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system",
                "content": (
                    "You are an HPC research assistant. "
                    "Answer only using the provided context. "
                    "For CSV contexts, complete row records preserve relationships between columns; "
                    "If the answer is not in the context, say you don't know."
                )},
            {
                "role": "user",
                "content": f"""
            Context:
            {context}

            Question:
            {question}
            """
            }
        ]
    )
    return response.choices[0].message.content