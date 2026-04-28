import argparse
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from gemini_config.call_function import available_functions, call_function
from gemini_config.prompts import system_prompt


def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")

    # Parse user input
    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # GEMINI client
    client = genai.Client(api_key=api_key)
    messages = [types.Content(role="user", parts=[types.Part(text=args.user_prompt)])]

    if args.verbose:
        print(f"User prompt: {args.user_prompt}")

    generate_content(client, messages, args.verbose)


# Using Gemini client, generate content based on user prompts
def generate_content(client, messages, verbose):
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
        ),
    )

    if not response.usage_metadata:
        raise RuntimeError("Gemini API Request Failed: No usage_metadata returned")

    if verbose:
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

    if not response.function_calls:
        print("Response:")
        print(response.text)
        return

    function_res = []
    for function_call in response.function_calls:
        function_call_result = call_function(function_call)

        if not function_call_result.parts:
            raise Exception("Error: types.Content object returned empty .parts list")
        if function_call_result.parts[0].function_response is None:
            raise Exception("Error: FunctionResponse object does not exist")
        if function_call_result.parts[0].function_response.response is None:
            raise Exception("Error: FunctionResponse object does not have a response")

        if verbose:
            print(f"-> {function_call_result.parts[0].function_response.response}")

        function_res.append(function_call_result.parts[0])


if __name__ == "__main__":
    main()
