# GitHub Upload Guide

## First Time Upload

### 1. Open Command Prompt

```bash
cd D:\10\proj\AudioDub
```

### 2. Initialize Git

```bash
git init
```

### 3. Add all files

```bash
git add .
```

### 4. Commit

```bash
git commit -m "Initial commit"
```

### 5. Rename branch to main

```bash
git branch -M main
```

### 6. Add GitHub repository

```bash
git remote add origin https://github.com/<username>/<repository>.git
```

Example:

```bash
git remote add origin https://github.com/devdatta1429/audio_dub.git
```

### 7. Upload to GitHub

```bash
git push -u origin main
```

---

# Second Time Upload (After Making Changes)

## 1. Go to project folder

```bash
cd D:\10\proj\AudioDub
```

## 2. Check changed files

```bash
git status
```

## 3. Add changes

```bash
git add .
```

## 4. Commit

```bash
git commit -m "Describe your changes"
```

Example:

```bash
git commit -m "Added translation feature"
```

## 5. Upload to GitHub

```bash
git push
```

That's it.

---

# Third Time (After Restarting the PC)

Restarting the PC does **NOT** affect your Git repository.

## 1. Open Command Prompt

```bash
cd D:\10\proj\AudioDub
```

## 2. Make your code changes

Save all files.

## 3. Check changes

```bash
git status
```

## 4. Add files

```bash
git add .
```

## 5. Commit

```bash
git commit -m "Describe what you changed"
```

Example:

```bash
git commit -m "Fixed audio synchronization"
```

## 6. Push to GitHub

```bash
git push
```

---

# Daily Git Workflow

```bash
cd D:\10\proj\AudioDub

git status

git add .

git commit -m "Your commit message"

git push
```

---

# Useful Commands

### Show changed files

```bash
git status
```

### Show commit history

```bash
git log --oneline
```

### Download latest changes from GitHub

```bash
git pull
```

### Check remote repository

```bash
git remote -v
```

---

# Notes

- `git init` is used **only once**.
- `git remote add origin ...` is used **only once**.
- `git branch -M main` is used **only once**.
- After the first upload, you only need:

```bash
git add .
git commit -m "Your message"
git push
```

Repeat these three commands whenever you want to upload new changes to GitHub.
