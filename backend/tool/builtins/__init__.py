from tool.builtins.clone_repo import clone_repo
from tool.builtins.list_directory import list_directory
from tool.builtins.query_github_analysis import query_github_analysis
from tool.builtins.read_file import read_file
from tool.builtins.read_resume import read_resume
from tool.builtins.read_skill import read_skill
from tool.builtins.save_real_question import save_real_question
from tool.builtins.save_repo_analysis import save_repo_analysis
from tool.builtins.search_code import search_code

TOOLS = [
    read_resume,
    query_github_analysis,
    read_skill,
    clone_repo,
    list_directory,
    read_file,
    search_code,
    save_repo_analysis,
    save_real_question,
]
