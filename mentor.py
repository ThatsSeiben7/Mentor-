import os
import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from prompts import get_system_instruction
from learner_model import calculate_user_level, update_stats

console = Console()

def configure_gemini():
    """Validates API key and configures the Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not found.")
        console.print("Please set it using: [cyan]export GEMINI_API_KEY='your_key'[/cyan]")
        exit(1)
    genai.configure(api_key=api_key)

def read_code_file(filepath: str) -> str:
    """Safely attempts to read the code file."""
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Could not find the file '{filepath}'.")
        exit(1)
    except Exception as e:
        console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
        exit(1)

def get_scaffolded_guidance(code: str, error_msg: str, user_level: str) -> dict:
    """Makes a SINGLE API call to Gemini requesting structured JSON containing 3 levels of help."""
   
    system_instruction = get_system_instruction(user_level)
   
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction,
        generation_config={"response_mime_type": "application/json"}
    )
   
    user_prompt = (
        f"Here is my code:\n```\n{code}\n```\n\n"
        f"Here is the error/issue I am facing:\n{error_msg}\n\n"
        f"Provide the 3 levels of progressive scaffolding in JSON."
    )

    with console.status(f"[bold green]Analyzing code & generating hints for a(n) {user_level} developer...", spinner="dots"):
        try:
            response = model.generate_content(
                user_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            return json.loads(response.text)
        except json.JSONDecodeError:
            console.print("[bold red]Error:[/bold red] Failed to parse model response as JSON.")
            exit(1)
        except Exception as e:
            console.print(f"[bold red]API Error:[/bold red] {str(e)}")
            exit(1)

def run_interactive_scaffolding(guidance: dict):
    """Interactively reveals the 3 tiers of help to the user and tracks progress."""
   
    # Tier 1: The Nudge
    console.print("\n")
    console.print(Panel(
        Markdown(guidance.get("level_1_nudge", "No nudge available.")),
        title="💡 Tier 1: Gentle Nudge",
        border_style="yellow",
        expand=False
    ))
   
    choice = Prompt.ask(
        "\n[bold yellow]Did that help you fix it?[/bold yellow] Press [green][Enter][/green] to reveal Tier 2 (Conceptual Hint), or type [bold cyan]'fixed'[/bold cyan] if you solved it",
        default="next"
    )
   
    if choice.strip().lower() in ["fixed", "f", "q", "quit"]:
        update_stats(tier_solved_at=1)
        console.print("\n[bold green]🎉 Awesome! Logged a Tier 1 solve. Your Learner Profile has been updated.[/bold green]\n")
        return

    # Tier 2: Intermediate help
    console.print("\n")
    console.print(Panel(
        Markdown(guidance.get("level_2_explanation", "No explanation available.")),
        title="🔍 Tier 2: Conceptual Breakdown",
        border_style="cyan",
        expand=False
    ))

    choice = Prompt.ask(
        "\n[bold cyan]Making sense now?[/bold cyan] Press [green][Enter][/green] to reveal Tier 3 (Full Solution), or type [bold cyan]'fixed'[/bold cyan] if you solved it",
        default="next"
    )

    if choice.strip().lower() in ["fixed", "f", "q", "quit"]:
        update_stats(tier_solved_at=2)
        console.print("\n[bold green]🎉 Great progress! Concept understood. Profile updated.[/bold green]\n")
        return

    # Tier 3: Fix
    console.print("\n")
    console.print(Panel(
        Markdown(guidance.get("level_3_solution", "No solution available.")),
        title="🛠️ Tier 3: Full Solution & Retrospective",
        border_style="green",
        expand=False
    ))
    update_stats(tier_solved_at=3)
    console.print("\n[bold green]Keep this retrospective in mind for your next build! Profile updated.[/bold green]\n")

def main():
    parser = argparse.ArgumentParser(description="Scaffold-AI: Progressive Coding Mentor")
    parser.add_argument("--file", type=str, help="Path to your broken Python script")
    parser.add_argument("--error", type=str, help="The error message you received")
   
    args = parser.parse_args()

    console.print(Panel.fit("[bold blue]🧠 Scaffold-AI: Progressive Adaptive Mentor[/bold blue]", border_style="blue"))

    filepath = args.file or Prompt.ask("📂 Enter the path to your broken code file")
    error_msg = args.error or Prompt.ask("🐛 Enter the error message or describe the bug")

    configure_gemini()
    code_content = read_code_file(filepath)
   
    # 1. Evaluate user level locally
    current_level = calculate_user_level()
   
    # 2. Make 1 single API call requesting all 3 tiers based on user level
    guidance = get_scaffolded_guidance(code_content, error_msg, current_level)

    # 3. Present interactively and log results
    run_interactive_scaffolding(guidance)

if __name__ == "__main__":
    main()
