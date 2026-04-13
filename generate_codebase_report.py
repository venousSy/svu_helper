import os

def generate_codebase_file():
    output_filename = "notebooklm_full_codebase.md"
    project_root = "."

    # Folders and files to completely ignore
    IGNORE_DIRS = {'.git', 'venv', 'env', '__pycache__', '.pytest_cache', '.agents', '.gemini', 'tmp', 'scratch', 'logs', '.ruff_cache', '.mypy_cache'}
    IGNORE_EXTS = {'.pyc', '.pyd', '.pyo', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.db', '.sqlite3', '.log', '.zip', '.tar', '.gz'}
    ALLOWED_EXTS = {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.env.example', '.toml', '.ini'}

    with open(output_filename, "w", encoding="utf-8") as outfile:
        outfile.write("# SVU Helper - Full Codebase Source\n\n")
        outfile.write("This document contains the entire current source code of the project, consolidated into a single file. ")
        outfile.write("Each section represents a file in the project, starting with its relative path. This structure allows AI models to understand the architecture and inter-dependencies of the codebase.\n\n")
        outfile.write("---\n\n")

        processed_count = 0

        for root, dirs, files in os.walk(project_root):
            # Modifying dirs in-place to prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

            for file in files:
                # Ignore the generator scripts and output files
                if file in [output_filename, "generate_notebooklm_git_report.py", "notebooklm_commit_history.md", "generate_codebase_report.py"]:
                    continue
                
                ext = os.path.splitext(file)[1].lower()
                
                is_valid = ext in ALLOWED_EXTS or file in ['Dockerfile', 'Makefile']
                if not is_valid:
                    continue

                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_root)
                rel_path = rel_path.replace("\\", "/") # Normalize path for markdown (cross-platform readable)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as infile:
                        content = infile.read()
                except Exception as e:
                    print(f"Skipping {rel_path} due to read error: {e}")
                    continue

                # Write to target file
                outfile.write(f"## File: `{rel_path}`\n\n")
                
                # Determine markdown language for syntax highlighting
                lang = "text"
                if ext == ".py": lang = "python"
                elif ext == ".json": lang = "json"
                elif ext in [".yaml", ".yml"]: lang = "yaml"
                elif ext == ".md": lang = "markdown"

                outfile.write(f"```{lang}\n")
                outfile.write(content)
                if not content.endswith("\n"):
                    outfile.write("\n")
                outfile.write(f"```\n\n---\n\n")
                processed_count += 1

    print(f"Codebase exported successfully! Processed {processed_count} files.\nSaved to: {output_filename}")

if __name__ == "__main__":
    generate_codebase_file()
