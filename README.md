# DSA San Diego Portal — Backend Handoff

> **Handoff document for TheSprinters → incoming team, May 2026**
> Original team: Akhil, Neil, Moiz (DNHS Computer Science, Period 2)
> Client: Deputy Sheriffs' Association of San Diego County — [dsasd.org](https://dsasd.org)

This Flask backend powers the DSASD member portal at `dsasd.opencodingsociety.com`. It provides sheriff-specific authentication, member management, an AI chatbot, and an events calendar — all built on top of the shared OCS Flask starter.

---

## DSASD Project Overview

The Deputy Sheriffs' Association (DSA) of San Diego County represents over 4,229 sworn deputies across 12 stations. We identified three critical failures on their existing WordPress site — broken login, invisible search, and 9+ cluttered menu items — and rebuilt their web presence as a modern single-page portal.

### What TheSprinters built

| Feature | Files | Status |
|---|---|---|
| Sheriff authentication (signup/login/logout) | `api/sheriff.py`, `model/sheriff.py` | ✅ Complete |
| JWT session management (`jwt_sheriff` cookie) | `api/sheriff.py` | ✅ Complete |
| Admin panel (view/delete members) | `api/sheriff.py` | ✅ Complete |
| AI chatbot (Claude/OpenAI API) | `api/sheriff_chat.py` | ✅ Complete |
| Events calendar API | `api/event_api.py` | ✅ Complete |
| Member profile (badge #, rank, station) | `model/sheriff.py` | ✅ Complete |

### DSASD-specific files (start here)

```
cap_back/
├── model/sheriff.py          # Sheriff SQLAlchemy model — sheriff_users table
├── api/sheriff.py            # Auth + CRUD endpoints (login, signup, admin)
├── api/sheriff_chat.py       # AI chatbot — Claude/OpenAI API integration
└── api/event_api.py          # Events calendar API
```

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/sheriff/authenticate` | Login → sets `jwt_sheriff` cookie |
| `DELETE` | `/api/sheriff/authenticate` | Logout → expires cookie |
| `GET` | `/api/sheriff/id` | Get current user from JWT |
| `POST` | `/api/sheriff/user` | Create new member (signup) |
| `GET` | `/api/sheriff/user` | List all members (admin only) |
| `PUT` | `/api/sheriff/user` | Update member profile |
| `DELETE` | `/api/sheriff/user` | Delete member (admin only) |
| `POST` | `/api/sheriff/chat` | AI chatbot → Claude/OpenAI API |

### Sheriff model fields

Badge/Sheriff ID, Name, UID, Password (hashed), Rank (Deputy/Corporal/Sergeant/Lieutenant/Captain), Station (all 12 SD County stations), Phone, Role (member/admin).

---

## Next Steps for the Incoming Team

These are the features TheSprinters planned but did not complete. They are listed in priority order.

### High priority

- **Connect the chatbot to the Anthropic Claude API** — the current `sheriff_chat.py` is wired to the OpenAI endpoint (`/v1/chat/completions`). The system prompt and message-history logic are already written; you just need to swap the API URL, auth header, and model name to use `claude-sonnet-4-6` or similar. Add `ANTHROPIC_API_KEY` to `.env`.
- **Persist RSVP data** — the RSVP buttons on the frontend events calendar toggle visually but don't write to the database. Add an `rsvp` table (or a column on the event model) and a `POST /api/event/rsvp` endpoint.
- **Email notifications** — there is a stub `api/email_service.py` already in the repo. Wire it to send a confirmation email when a member RSVPs or when a new newsletter is posted.

### Medium priority

- **WordPress API sync** — pull live news and newsletter data from dsasd.org's WordPress REST API (`dsasd.org/wp-json/wp/v2/posts`) instead of the static hardcoded cards on the frontend.
- **Document center** — add an S3-backed file upload/download endpoint so members can access contracts, MOU PDFs, and forms without leaving the portal. There are stubs for S3 in `testing/s3tests.py`.
- **Personalized dashboard** — use the JWT `rank` and `station` claims to return station-specific news and events from the API. The frontend already reads these fields on login.

### Lower priority / stretch goals

- **Push notifications** — a `service-worker.js` already exists in the frontend. Add a Web Push subscription endpoint to the backend and trigger pushes when new events or newsletters are created.
- **ML content recommendations** — log tile-click and search interactions to an `analytics` table, then train a collaborative-filtering model (scikit-learn) to reorder dashboard tiles per member. Serve predictions from `/api/sheriff/recommendations`.
- **WCAG 2.1 AA accessibility audit** — run an automated audit (axe-core or Lighthouse) and address keyboard navigation gaps and ARIA label coverage.
- **Production database migration** — the portal currently runs SQLite. When dsasd.org is ready to adopt the portal, migrate to AWS RDS (PostgreSQL) using the existing `scripts/db_migrate-prod2sqlite.py` and `db_restore-sqlite2prod.py` scripts.

---

## Environment Setup

Copy `.env.example` (or use the template below) and fill in your own keys. **Never commit `.env` to git.**

```shell
# Flask
IS_PRODUCTION=false
FLASK_PORT=8587

# Admin defaults
DEFAULT_PASSWORD='YourPassword!'
ADMIN_USER='Admin Name'
ADMIN_UID='admin'
ADMIN_PASSWORD='AdminPass!'

# AI Chatbot — pick one
ANTHROPIC_API_KEY=sk-ant-xxxxx        # preferred (Claude API)
# or
OPENAI_API_KEY=sk-xxxxx               # fallback (GPT-4o-mini)

# AWS S3 (for document center — future)
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_S3_BUCKET=dsasd-documents

# GitHub
GITHUB_TOKEN=ghp_xxx
```

---

## Deployment

The backend runs on AWS EC2 behind NGINX with Let's Encrypt SSL. To redeploy after pulling changes:

```bash
# On the EC2 instance
git pull
docker-compose down && docker-compose up -d --build
```

NGINX config is at `nginx_for_flask_8587`. The frontend at `dsasd.opencodingsociety.com` proxies `/api/*` requests to this backend on port 8587.

---

## License

This project is licensed under the Apache License 2.0. See [`LICENSE`](./LICENSE).

The DSASD-specific code (sheriff auth, chatbot, events API) was authored by Akhil, Neil, and Moiz as a community contribution to the Deputy Sheriffs' Association of San Diego County through DNHS Computer Science. Long-term hosting, maintenance, and operational costs would need to be negotiated separately with the organization.



## Flask Portfolio Starter

Use this project to create a Flask Server.

- GitHub link: [flask](https://github.com/open-coding-society/flask), runtime link is published under the About on this same page.
- `Use this as template` option is availble if you plan on making your instance of the repository.
- `Fork` the repository if you plan to contribute though GitHub PRs.

## The conventional way to get started

> Quick steps that can be used with MacOS, WSL Ubuntu, or Ubuntu; this uses Python 3.9 or later as a prerequisite.

- Open a Terminal, clone a project and `cd` into the project directory.  Use a `different link` and name for `name` for clone to match your repo.

```bash
mkdir -p ~/openccs; cd ~/opencs

git clone https://github.com/open-coding-ocietyflask.git

cd flask
```

- Install python dependencies for Flask, etc.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Open project in VSCode

- Prepare VSCode and run
  - From Terminal run VSCode

  ```bash
  code .
  ```

  - Open Setting: Ctrl-Shift P or Cmd-Shift
    - Search Python: Select Interpreter.
    - Match interpreter to `which python` from terminal.
    - Shourd be ./venv/bin/python

  - From Extensions Marketplace install `SQLite3 Editor`
    - Open and view SQL database file `instance/volumes/user_management.db`

  - Make a local `.env` file in root of project to contain your secret passwords

  ```shell
  # Port configuration
  # FLASK_PORT=8001
  # Admin user reset password 
  DEFAULT_PASSWORD='123Qwerty!'
  DEFAULT_PFP='default.png'
  # Admin user defaults
  ADMIN_USER='Thomas Edison'
  ADMIN_UID='toby'
  ADMIN_PASSWORD='123Toby!'
  ADMIN_PFP='toby.png'
  # Teacher user defaults
  TEACHER_USER='Nikola Tesla'
  TEACHER_UID='niko'
  TEACHER_PASSWORD='123Niko!'
  TEACHER_PFP='niko.png'
  # Default user for testing 
  USER_NAME='Grace Hopper'
  USER_UID='hop'
  USER_PASSWORD='123Hop!'
  USER_PFP='hop.png'
  # Convience user defaults
  MY_NAME='John Mortensen'
  MY_UID='jm1021'
  MY_ROLE='admin'
  # Obtain key, [Google AI Studio](https://aistudio.google.com/api-keys)
  GEMINI_API_KEY=xxxxx
  GEMINI_SERVER=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
  # Obtain key, [Groq Console](https://console.groq.com/keys)
  GROQ_API_KEY=xxxxx
  GROQ_SERVER=https://api.groq.com/openai/v1/chat/completions
  # GitHub Configuation
  GITHUB_TOKEN=ghp_xxx
  GITHUB_TARGET_TYPE=user  # Use 'organization' or 'user'
  GITHUB_TARGET_NAME=Open-Coding-Society
  # KASM Configuration (server is defaulted)
  KASM_SERVER=https://kasm.opencodingsociety.com
  KASM_API_KEY_SECRET=xxxx
  KASM_API_KEY=xxx
  # DB Configuration, AWS RDS
  IS_PRODUCTION=false # false = LOCAL true = DEPLOYED
  DB_USERNAME='admin'
  DB_PASSWORD='xxxxx'
  ```

  - Make the database and init data.
  
  ```bash
  ./scripts/db_init.py
  ```

  - Explore newly created SQL database
    - Navigate too instance/volumes
    - View/open `user_management.db`
    - Loook at `users` table in viewer

  - Run the Project
    - Select/open `main.py` in VSCode
    - Start with Play button
      - Play button sub option contains Debug
    - Click on localhost:8087 in terminal to launch
      - Output window will contain page to launch http://localhost:8325
    - Login using your secrets from env

  - Basic API test
    - [Jokes](http://localhost:8325/api/jokes/)

### User Operations
| Purpose | Correct Endpoint | What It Does |
|---------|-----------------|--------------|
| **Login** | `/api/authenticate` | Authenticates user & sets cookie |
| **Get User** | `/api/id` | Gets current logged-in user |
| **Signup** | `/api/user` | Creates new user account |
| **Posts** | `/api/post/all` | Gets all social media posts |
| **Create Post** | `/api/post` | Creates a new post |
| **Gemini AI** | `/api/gemini` | Chat with AI assistant |

### MicroBlog Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/microblog` | Create new post |
| GET | `/api/microblog` | Get posts (with filters) |
| PUT | `/api/microblog` | Update post |
| DELETE | `/api/microblog` | Delete post |

**Query Parameters for GET:**
- `?topicId=1` - Posts for specific topic
- `?userId=123` - Posts by specific user  
- `?search=flask` - Search content
- `?limit=20` - Limit results

### MicroBlog Interactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/microblog/reply` | Add reply to post |
| POST | `/api/microblog/reaction` | Add reaction (👍, ❤️, etc.) |
| DELETE | `/api/microblog/reaction` | Remove reaction |

### Microblog Page Integration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/microblog/page/<page_key>` | Get posts for specific page |
| POST | `/api/microblog/topics/auto-create` | Auto-create topic for page |
| GET | `/api/microblog/topics?pagePath=X` | Get topic by page path |

## Idea

### Files and Directories in this Project

The key files and directories in this project are in these online articles.

[Python/Flask](https://pages.opencodingsociety.com/python/flask)

[Legacy - Flask Intro](https://pages.opencodingsociety.com/flask-overview)



## Database Management Workflow with Scripts

If you are working with the database, follow the below procedure to safely interact with the remote DB while applying changes locally. Certain scripts require flask to be running while others don't, so follow the instructions that the scripts provide.

Note, steps 1,2,3,5 are on your development (LOCAL) server. You need to update your .env on development server and be sure all PRs are completed, pulled, and tested before you start pushing to production.

0. Be sure ADMIN_PASSWORD is set in .env.  You will need a venv for the python scripts.

1. Initialize your local DB with clean data. For example, this would be good to see that a schema update works correctly.
   ```bash
   python scripts/db_init.py
   ```

2. Pull the database content from the remote DB onto your local machine. This allows you to work with real data and test that real data works with your local changes.
   ```bash
   python scripts/db_migrate-prod2sqlite.py
   ```

3. TEST TEST TEST! Make sure your changes work correctly with the local DB.

4. Now go onto the remote DB and back up the db using `cp sqlite.db backups/sqlite_year-month-day.db` in the volumes directory of the flask directory on cockpit. Then, run `git pull` to ensure that flask has been updated with the latest code. Then, run `python scripts/db_init.py` again to ensure that the remote DB schema is up to date with the latest code.

5. Once you are satisfied with your changes, push the local DB content to the remote DB. This requires authentication, so you need to replace the ADMIN_PASSWORD in the .env file of "flask" with the production admin password.
   ```bash
   python scripts/db_restore-sqlite2prod.py
   ```

### Condensed DB/Schema update simple steps
*(a copy of what's above, just condensed)*

1. Initialize local DB: `python scripts/db_init.py`

2. Pull production data to local: `python scripts/db_migrate-prod2sqlite.py`

3. Test your changes locally

4. On production server (in cockpit):
   - Backup DB in volumes directory: `cp sqlite.db backups/sqlite_year-month-day.db`
   - Update code: `git pull`
   - Update schema: `python scripts/db_init.py`

5. Push local changes to production: `python scripts/db_restore-sqlite2prod.py` (Requires admin password from production in .env)
