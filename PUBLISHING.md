# NESR Logic — Publication & Release Guide

This document provides step-by-step instructions for publishing **NESR Logic** (`nesr-logic`) to GitHub, TestPyPI, and the official Python Package Index (PyPI).

> [!IMPORTANT]
> In accordance with safety policies, public release must only occur with explicit authorization. Do not publish without developer approval.

---

## 1. Pre-Release Verification Checklist

Before publishing, verify all build artifacts and tests pass locally:

- [x] Run test suite: `pytest -v` (all 20 tests pass)
- [x] Verify core lines of code (< 200 nonblank, non-comment lines): `python tools/count_sloc.py` (179 SLOC)
- [x] Verify clean builds: `python -m build`
- [x] Validate metadata with Twine: `python -m twine check dist/*` (PASSED)
- [x] Test installation in clean virtual environment (`test_env`)

---

## 2. GitHub Publication Checklist

### Step 2.1: Initialize Git Repository (if not already done)

```bash
git init
git add .
git commit -m "feat: initial release of nesr-logic v0.1.0"
```

### Step 2.2: Add Remote and Push to GitHub

```bash
git branch -M main
git remote add origin https://github.com/nesr-logic/nesr-logic.git
git push -u origin main
```

### Step 2.3: Tag Release and Create GitHub Release

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

On GitHub:
1. Navigate to **Releases** > **Draft a new release**.
2. Select tag `v0.1.0`.
3. Set title: `NESR Logic v0.1.0`.
4. Paste release notes from `CHANGELOG.md`.
5. Attach `dist/nesr_logic-0.1.0-py3-none-any.whl` and `dist/nesr_logic-0.1.0.tar.gz`.
6. Click **Publish release**.

---

## 3. TestPyPI Publication Instructions

TestPyPI allows verifying the release process on a sandbox repository before publishing to production PyPI.

### Step 3.1: Configure TestPyPI API Token

Create an account on [https://test.pypi.org/](https://test.pypi.org/) and generate an API token (`pypi-...`).

### Step 3.2: Upload Artifacts to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

Enter `__token__` as the username and your TestPyPI API token as the password.

### Step 3.3: Verify TestPyPI Installation

In a temporary directory or clean virtual environment, verify installation from TestPyPI:

```bash
python -m venv test_pypi_env
.\test_pypi_env\Scripts\activate  # On Windows pwsh/cmd
# or source test_pypi_env/bin/activate on Linux/macOS

pip install --index-url https://test.pypi.org/simple/ --no-deps nesr-logic

# Verify CLI
nesr-logic --help

# Verify Python import
python -c "import nesr_logic; print(nesr_logic.__version__)"
```

---

## 4. Official PyPI Release Instructions

Once TestPyPI verification is confirmed and explicit release authorization is given:

### Step 4.1: Upload Artifacts to PyPI

```bash
python -m twine upload dist/*
```

Enter `__token__` as the username and your production PyPI API token (`pypi-...`) as the password.

### Step 4.2: Verify Production Installation

```bash
python -m venv prod_test_env
.\prod_test_env\Scripts\activate

pip install nesr-logic==0.1.0

# Verify CLI execution
nesr-logic scan --help

# Verify programmatic scan
python -c "import nesr_logic; report = nesr_logic.scan('.'); print(report.summary())"
```

---

## 5. Security & Maintenance Notes

- Never commit PyPI tokens, secrets, or credentials to version control.
- Use Trusted Publishing (OIDC) with GitHub Actions for automated, keyless PyPI releases on tag creation.
- Check PyPI project page after publication: `https://pypi.org/project/nesr-logic/`.
