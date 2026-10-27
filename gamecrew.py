import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv('GEMINI_API_KEY')
serper = os.getenv("SERPER_API_TOOL")


# write your code here
from crewai import Agent, Task, Crew, Process, LLM 
from crewai_tools import SerperDevTool
import sys
import subprocess
import re
from pathlib import Path

llm = LLM(
   model="gemini/gemini-2.5-flash",
   api_key=gemini_api_key
)

search_tool = SerperDevTool()

game_designer = Agent(
    role="Creative Game Designer",
    goal="Come up with fun, feasible game concepts and detailed mechanics based on user idea",
    backstory=
      "You are an experienced game designer."
      "You excel at turning vague ideas into clear, exciting game designs including:"
      "- core loop, rules, win/lose conditions"
      "- basic entities (player, enemies, items)"
      "- controls and feel"
      "Keep it simple enough to implement in pure Python + Pygame in one file.",
    verbose=True,
    llm=llm,
    tools=[search_tool]
)

senior_engineer = Agent(
   role="Senior Python Game Developer",
   goal="Write clean, working Python code (using Pygame) for the described game",
    backstory=
        "You are a senior software engineer specialized in Python game development with Pygame."
        "You write structured, readable code with:"
        "- Proper game loop, event handling, drawing"
        "- Comments explaining key parts"
        "- Error handling where needed"
        "You always produce a complete, runnable .py file.",
   verbose=True,
   llm=llm,
   tools=[search_tool]
)

qa_engineer = Agent(
    role="QA Engineer & Code Reviewer",
    goal="Test, review, and improve the code for bugs, playability, and completeness",
    backstory=
        "You are a meticulous QA engineer and code reviewer."
        "You carefully check:"
        "- Does the code run without errors?"
        "- Does it implement ALL the designed features?"
        "- Is it fun/playable? Any obvious balance issues?"
        "- Code style, variable names, comments"
        "Suggest fixes or small improvements and output the FINAL improved code.",
    verbose=True,
    llm=llm,
)

task_design = Task(
    description=
        "Take the user's game idea: {game_idea}"
        "1. Clarify and expand it into a fun, simple 2D game"
        "2. Describe: objective, controls, entities, win/lose"
        "3. Keep scope small (one level, basic mechanics)"
        "Output format:"
        "## Game Design Document"
        "- Title: ..."
        "- Genre: ..."
        "- Objective: ..."
        "- Controls: ..."
        "- Entities: ..."
        "- Mechanics: ...",
    expected_output="A clear markdown Game Design Document",
    agent=game_designer
)

task_code = Task(
    description=
        "Using the game design from the previous task"
        "Write a COMPLETE, standalone Python script using Pygame that implements the game."
        "- Include import pygame, sys, random (if needed)"
        "- Full game loop, init, events, update, draw"
        "- Make it runnable with python game.py"
        "- Add simple comments"
        "- The main game loop must be exposed in the python code, it should not be inside any function like main"
        "- Final answer MUST be ONLY the Python code and Instructions on how to play the game",
    expected_output="A complete runnable Pygame Python script",
    agent=senior_engineer,
    context=[task_design]
)

task_review = Task(
    description=
        "Review the Python code from the previous task."
        "1. Check for syntax/runtime errors"
        "2. Verify it matches the design document"
        "3. Test mentally: does it have init, loop, quit handling, drawing?"
        "4. Suggest fixes/improvements if needed"
        "5. Output the FINAL, improved, ready-to-run code"
        "Your final answer MUST be ONLY the complete Python code along with the instructions on how to play the game",
    expected_output="Final polished, runnable Pygame Python script and instructions on how to play the game",
    agent=qa_engineer,
    context=[task_design, task_code]
)


game_crew = Crew(
    agents=[game_designer, senior_engineer, qa_engineer],
    tasks=[task_design, task_code, task_review],
    process=Process.sequential,
    verbose=True
)

game_idea = "A fun endless runner where a character jumps over obstacles"
result = game_crew.kickoff(inputs={"game_idea": game_idea})
print(result)

generated_output = str(result)

# Extract Python code if it is inside a Markdown code block
match = re.search(
    r"```(?:python)?\s*\n(.*?)```",
    generated_output,
    re.DOTALL | re.IGNORECASE
)

if not match:
    raise ValueError("No Python code block found in CrewAI output.")

game_code = match.group(1).strip()

# Save the generated game
game_file = Path(__file__).parent / "game.py"
game_file.write_text(game_code + "\n", encoding="utf-8")

print(f"Game saved to: {game_file}")

# Launch the generated game in a separate process
subprocess.Popen(
    [sys.executable, str(game_file)],
    cwd=str(game_file.parent)
)

print("Game launched!")
