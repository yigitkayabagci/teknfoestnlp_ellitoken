from huggingface_hub import login
login(new_session=False)

# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("image-text-to-text", model="google/gemma-3-27b-it")
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Who are you?"}
        ]
    },
]
pipe(text=messages)