Now that your repository is connected to GitHub, every time you make changes locally, the workflow is simple.

1. Check what changed
git status

2. Stage the changes

To stage everything:

git add .


Or stage a specific file:

git add path/to/file.py

3. Commit the changes

Write a meaningful commit message:

git commit -m "Describe what you changed"


Examples:

git commit -m "Add translation improvements"
git commit -m "Fix Streamlit UI bug"
git commit -m "Update audio alignment pipeline"

4. Push to GitHub
git push


Since you've already set the upstream with git push -u origin main, you don't need to specify origin main again. Just git push is enough.

Complete workflow
git status
git add .
git commit -m "Your commit message"
git push

If you only want to see what changed
git diff


Or see which files changed:

git status

If Git says "nothing to commit"

It means either:

You haven't modified any tracked files, or
You forgot to save the files before committing.
One recommendation for your repository

Your first commit includes files under data/projects/ (videos, WAV files, outputs, etc.). Those can make the repository very large. If these are generated or temporary files, consider adding them to .gitignore so future commits don't keep uploading them.

For example:

data/projects/
.venv/
__pycache__/
*.wav
*.mp4


If you want to keep only the source code on GitHub and exclude generated audio/video outputs going forward, I can help you clean up the repository without affecting your local files.