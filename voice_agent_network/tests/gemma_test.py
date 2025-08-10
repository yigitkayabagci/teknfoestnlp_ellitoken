from llm.llm_models import Gemma
from llm import Device
medgemma = Gemma(False, model_variant= Gemma.Variant.GEMMA_3_1B_IT, device_map= Device.AUTO)

#EXAMPLE
def print_example():
    role_instruction = "You are a helpful assistant."
    prompt = "Ankara hangi ülkede?"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ]
        }
    ]

    print("--- Running initial example ---")
    print(f"System: {role_instruction}")
    print(f"User: {prompt}")
    print(f"MedGemma: {medgemma.give_prompt(messages)}")
    print("--- End of initial example ---")
print_example()


while True:
    print("\n--- New conversation ---")

    sys_prompt = input("System prompt ('quit' to exit): ")
    if sys_prompt.lower() == 'quit':
        print("Exiting conversation.")
        break

    user_prompt = input("User prompt ('quit' to exit): ")
    if user_prompt.lower() == 'quit':
        print("Exiting conversation.")
        break

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": sys_prompt}]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
            ]
        }
    ]

    # Generate and print the response
    print(f"MedGemma: {medgemma.give_prompt(messages)}")