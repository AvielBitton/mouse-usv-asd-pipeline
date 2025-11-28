# 🔧 Environment Setup (Python 3.8)

This project requires **Python 3.8** and a clean virtual environment.

## 1. Install Python 3.8

### Linux (Ubuntu)

```bash
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-distutils
```

### macOS (Homebrew)

```bash
brew install python@3.8
```

### Windows

Install Python 3.8 from:
[https://www.python.org/downloads/release/python-380/](https://www.python.org/downloads/release/python-380/)

---

## 2. Create a virtual environment

In the project folder:

```bash
python3.8 -m venv .venv
```

Activate it:

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
.\venv\Scripts\activate
```

Check version:

```bash
python -V
```

Should show **Python 3.8.x**

---

## 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ✔ Done

Your environment is ready.
