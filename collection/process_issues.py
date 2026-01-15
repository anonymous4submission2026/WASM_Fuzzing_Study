import json
import re
import os
import sys
import requests

def download_file(url, directory):
    """
    Downloads the file from the URL and saves it in the specified directory.
    Returns the local file path.
    """
    # Extract file name from URL (remove any query parameters)
    local_filename = url.split('/')[-1].split('?')[0]
    file_path = os.path.join(directory, local_filename)
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded file from {url} to {file_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
    return file_path

def process_issues(issues_directory):
    """
    Loads the issues JSON, filters issues with comments that have any of the target keywords,
    extracts code blocks in triple backticks and links to certain file types,
    and then downloads/stores the files/code blocks in a dedicated directory for each issue.
    """
    # Define keywords to trigger processing
    keywords = ["bug", "failure", "error", "fault", "inconsistent", "different", "sigsegv", "segfault"]
    keyword_pattern = re.compile("|".join(keywords), re.IGNORECASE)
    
    # Regex pattern to extract code blocks with an optional language identifier.
    # It captures:
    #   group(1): language (if provided) right after ```
    #   group(2): the code content until the closing ```
    code_block_pattern = re.compile(r"```(?:([\w+\-\.]+)?\s*\n)?(.*?)```", re.DOTALL)
    
    # Regex to match URLs to files with specific extensions (tar, tar.gz, zip, wasm, aot, txt, wat)
    file_exts = r"(?:tar(?:\.gz)?|zip|wasm|aot|txt|wat)"
    link_pattern = re.compile(r"(https?://\S+\." + file_exts + r")", re.IGNORECASE)
    
    issues_file = os.path.join(issues_directory, "issues.json")
    # Load the JSON file with issues data
    try:
        with open(issues_file, "r") as f:
            issues_data = json.load(f)
    except Exception as e:
        print(f"Error reading {issues_file}: {e}")
        return

    # Process each issue by its number
    for issue_number, issue_detail in issues_data.items():
        comments = issue_detail.get("comments", [])
        issue_triggered = False
        code_blocks = []  # List of tuples: (extension, code)
        file_links = []

        # Check the issue title for keywords.
        title = issue_detail.get("title", "")
        if keyword_pattern.search(title):
            issue_triggered = True

        # Check the issue body for keywords.
        body = issue_detail.get("body", "")
        if keyword_pattern.search(body):
            issue_triggered = True

        # Extract code blocks and file links from the issue body.
        found_body_codes = code_block_pattern.findall(body)
        if found_body_codes:
            for lang, block in found_body_codes:
                block = block.strip()
                if lang:
                    ext = lang.lower()
                else:
                    lower_block = block.lower()
                    ext = "wat" if "module" in lower_block and "func" in lower_block else "txt"
                code_blocks.append((ext, block))
        found_body_links = link_pattern.findall(body)
        if found_body_links:
            file_links.extend(found_body_links)
        
        # Evaluate each comment for the keywords, code blocks, and file links.
        for comment in comments:
            comment_body = comment.get("body", "")
            # If any keyword is found, mark issue as triggered
            if keyword_pattern.search(comment_body):
                issue_triggered = True

                # Extract code blocks with optional language identifier.
                found_code = code_block_pattern.findall(comment_body)
                if found_code:
                    for lang, block in found_code:
                        block = block.strip()
                        # Determine the file extension for the code block.
                        if lang:
                            # Use the language name (lowercased) as the extension.
                            ext = lang.lower()
                        else:
                            # No language provided – use a heuristic to detect WAT code.
                            lower_block = block.lower()
                            if "module" in lower_block and "func" in lower_block:
                                ext = "wat"
                            else:
                                ext = "txt"
                        code_blocks.append((ext, block))
                
                # Extract file links if present.
                found_links = link_pattern.findall(comment_body)
                if found_links:
                    file_links.extend(found_links)
        
        # Only proceed if the issue was triggered and we have at least one code block or file link.
        if issue_triggered and (code_blocks or file_links):
            target_dir = os.path.join(issues_directory, str(issue_number))
            os.makedirs(target_dir, exist_ok=True)
            print(f"Processing issue {issue_number}: created directory {target_dir}")

            # Download the complete issue page as HTML.
            issue_url = issue_detail.get("url")
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(issue_url, headers=headers)
                response.raise_for_status()
                html_file_path = os.path.join(target_dir, "{0}.html".format(issue_number))
                with open(html_file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Saved issue page to {html_file_path}")
            except Exception as e:
                print(f"Error downloading issue HTML for issue {issue_number}: {e}")

            # Save each extracted code block with its determined extension.
            for idx, (ext, code) in enumerate(code_blocks, start=1):
                file_name = f"code_block_{idx}.{ext}"
                file_path = os.path.join(target_dir, file_name)
                try:
                    with open(file_path, "w") as f:
                        f.write(code)
                    print(f"Saved code block to {file_path}")
                except Exception as e:
                    print(f"Error writing code block file {file_path}: {e}")
            
            # Download all files from links.
            for url in file_links:
                download_file(url, target_dir)
        else:
            print(f"Skipping issue {issue_number}: no relevant code blocks or file links found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_issues.py <issues_directory>")
        sys.exit(1)
    issues_directory = sys.argv[1]
    process_issues(issues_directory)

