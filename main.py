"""
CLI entry point. Requires Ollama running locally
with the models named in config.py pulled.
"""

import json
from orchestrator import handle_user_message

if __name__ == "__main__":
    print("Endpoint security validation bot. Type 'exit' to quit.\n")
    while True:
        user_input = input("> ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        result = handle_user_message(user_input)
        print(json.dumps(result, indent=2, default=str))
        print()
