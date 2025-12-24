# PyPI Trusted Publishing Setup

This repository uses GitHub Actions OIDC (Trusted Publishing) to publish releases to TestPyPI and PyPI without long-lived password tokens.

## 1. Create GitHub Environments

In this repository's **Settings -> Environments**, create two environments:

1.  **`testpypi`**
    *   No protection rules (automatic deployment).
2.  **`pypi`**
    *   **Required reviewers**: Add yourself or the maintainer team. This acts as the "Promotion Gate" for production releases.

## 2. Configure PyPI (Trusted Publishing)

You must configure the trust relationship on PyPI so it accepts tokens from this GitHub repo's workflows.

### A. TestPyPI Setup

1.  Log in to [TestPyPI](https://test.pypi.org/).
2.  Go to your Project Settings (or create the project if it doesn't exist).
3.  **Publishing -> Trusted Publishers -> Add**.
4.  **Owner**: `{your-github-org}`
5.  **Repository**: `django-automate`
6.  **Workflow name**: `release.yml`
7.  **Environment**: `testpypi`

### B. PyPI Production Setup

1.  Log in to [PyPI](https://pypi.org/).
2.  Go to Project Settings.
3.  **Publishing -> Trusted Publishers -> Add**.
4.  **Owner**: `{your-github-org}`
5.  **Repository**: `django-automate`
6.  **Workflow name**: `release.yml`
7.  **Environment**: `pypi`

## 3. How to Release

1.  Draft your changes.
2.  Tag a version:
    ```bash
    git tag v0.1.0
    git push origin v0.1.0
    ```
3.  The **Release** workflow will:
    *   Build artifacts.
    *   Deploy to **TestPyPI**.
    *   Pause and wait for approval on the **PyPI** environment (check "Deployments" sidebar).
    *   Once approved, publish to **PyPI** and create a **GitHub Release**.
