# CIRCULINK — Flask-only Vercel build

This release is a Python/Flask application.

## Runtime
- Flask application entrypoint: `api/index.py`
- WSGI entrypoint: `wsgi.py`
- Local runner: `run.py`
- Python dependencies: `requirements.txt`
- Vercel Python builder: `@vercel/python` in `vercel.json`

## Node.js
Node.js/npm are **not required** to run or deploy this CIRCULINK application.
There is no `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, or Node server in this release.

The JavaScript files under `static/` are browser-side assets only (maps, UI interactions, validation, etc.); they are served as static files and are not a Node runtime.

## Production
Import this repository into Vercel as a Python project. Configure the environment variables in `.env.example`, especially `SECRET_KEY`, MongoDB, Daraja, Cloudinary and SMTP settings.

MongoDB transactions used by checkout require a deployment that supports MongoDB sessions/transactions, such as MongoDB Atlas with the appropriate replica-set topology.
