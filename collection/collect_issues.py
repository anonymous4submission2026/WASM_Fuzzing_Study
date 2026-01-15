import subprocess
import json
import sys
import os

def collect_issues_and_comments(owner, repo, limit):
    """
    Collects issues and their discussions/comments from a GitHub repository using the gh CLI.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        limit (int): The maximum number of issues to retrieve.

    Returns:
        dict: A dictionary where keys are issue numbers and values are the issue details including comments.
    """
    repository = f"{owner}/{repo}"
    issues_data = {}

    try:
        # Retrieve the list of issues as JSON containing issue numbers.
        # Filter for issues with "bug" or "Bug" labels
        list_cmd = [
            'gh', 'issue', 'list',
            '--repo', repository,
            '--state', 'all',
            '--limit', str(limit),
            '--label', 'bug,Bug',
            '--json', 'number'
        ]
        list_output = subprocess.check_output(list_cmd)
        issues = json.loads(list_output)
        print(f"Retrieved {len(issues)} issues from {repository}")
    except subprocess.CalledProcessError as e:
        print("Error while listing issues:", e)
        return {}
    except Exception as e:
        print("Unexpected error:", e)
        return {}

    # For each issue number, retrieve detailed info and comments.
    for i, issue in enumerate(issues, 1):
        issue_number = issue.get("number")
        if issue_number is None:
            continue
        
        print(f"Processing issue {i}/{len(issues)}: #{issue_number}")
        
        try:
            view_cmd = [
                'gh', 'issue', 'view', str(issue_number),
                '--repo', repository,
                '--comments',
                '--json', 'number,url,title,body,comments'
            ]
            view_output = subprocess.check_output(view_cmd)
            issue_detail = json.loads(view_output)
            issues_data[issue_number] = issue_detail
        except subprocess.CalledProcessError as e:
            print(f"Error while viewing issue {issue_number}:", e)
        except Exception as e:
            print(f"Unexpected error for issue {issue_number}:", e)

    return issues_data

def store_issues_json(owner, repo, limit, output_file="issues.json"):
    """
    Collects issues and their comments from a specified GitHub repo and stores the result in a JSON file.

    Args:
        owner (str): Repository owner.
        repo (str): Repository name.
        limit (int): Maximum number of issues to retrieve.
        output_file (str): The filename where the JSON output will be stored.
    """
    data = collect_issues_and_comments(owner, repo, limit)
    try:
        with open(output_file, "w") as fp:
            json.dump(data, fp, indent=2)
        print(f"Issues and comments have been successfully saved to {output_file}")
        print(f"Total issues collected: {len(data)}")
    except IOError as e:
        print("Error writing JSON to file:", e)

# Example usage:
if __name__ == "__main__":
    owner = sys.argv[1]   # Replace with the actual repository owner
    repo  = sys.argv[2]    # Replace with the actual repository name
    limit = int(sys.argv[3])
    storage_dir = sys.argv[4]  # Directory path to store issues.json

    store_issues_json(owner, repo, limit, os.path.join(storage_dir, "issues.json"))