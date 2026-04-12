import subprocess
import sys

def generate_report():
    output_filename = "notebooklm_commit_history.md"

    # Get a list of commit hashes chronologically
    try:
        # %H is full hash
        result = subprocess.run(
            ['git', 'log', '--reverse', '--pretty=format:%H'],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print("Error running git log:", e)
        return

    commit_hashes = result.stdout.strip().split('\n')
    total_commits = len(commit_hashes)
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("# SVU Helper - Git Commit History\n\n")
        f.write("This document contains the chronological commit history of the repository, including commit hashes, messages, and code differences (diffs). It is formatted for optimal parsing by AI models like NotebookLM.\n\n")
        f.write("---\n\n")
        
        for i, commit_hash in enumerate(commit_hashes):
            if not commit_hash:
                continue
                
            print(f"Processing commit {i+1}/{total_commits}: {commit_hash[:7]}")
            
            # Get commit metadata: ISO 8601 Date format followed by raw body
            metadata_result = subprocess.run(
                ['git', 'show', '-s', '--format=%cI%n%B', commit_hash],
                capture_output=True, text=True, errors='replace'
            )
            
            out_str = metadata_result.stdout if metadata_result.stdout else ""
            lines = out_str.strip().split('\n', 1)

            date = lines[0] if len(lines) > 0 else "Unknown Date"
            message = lines[1].strip() if len(lines) > 1 else "No message"
            
            # Get commit diff without logging metadata again
            diff_result = subprocess.run(
                ['git', 'show', '--format=', '-p', commit_hash],
                capture_output=True, text=True, errors='replace'
            )
            diff = diff_result.stdout.strip() if diff_result.stdout else ""

            
            f.write(f"## Commit: `{commit_hash}`\n")
            f.write(f"**Date:** {date}\n\n")
            f.write("### Message\n")
            f.write(f"```text\n{message}\n```\n\n")
            
            if diff:
                f.write("### Code Changes (Diff)\n")
                f.write(f"```diff\n{diff}\n```\n\n")
            else:
                f.write("### Code Changes (Diff)\n")
                f.write("*No code changes in this commit.*\n\n")
                
            f.write("---\n\n")

    print(f"\nReport generated successfully! Saved to: {output_filename}")

if __name__ == "__main__":
    generate_report()
