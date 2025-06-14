# Welcome to newSumma 👋

> A real-time solution for collecting and summarizing Vietnamese news.

---

## 🧠 About the Project

**newSumma** is a full-stack system developed as a university thesis project to automatically **collect**, **summarize**, and **serve Vietnamese news in real time**. It leverages modern technologies such as Django, React, Celery, and Docker to ensure scalability and maintainability, with news summarization powered by Meta Llama 3.2 (see [License](#-license) for details).

The system includes:

- 🔎 **Real-time news scraper** using Selenium
- 🧠 **Automatic news summarization** powered by LLM (LLaMA 3.2 1B)
- 📊 **User-personalized ranking** based on reading duration, clicks, and preferences
- ⚙️ **Modular backend architecture** with clear separation of concerns (crawler, summarizer, recommender, user)
- 🔁 **Task scheduling** using Celery with 2 workers and 1 beat process
- 📦 **Dockerized environment** for full deployment using Docker Compose
- 🌐 **RESTful API** for frontend consumption
- 💾 **PostgreSQL** for relational data storage
- 🧠 **Caching and softmax logic** to prevent memory overflow and speed up personalized scoring

---

## 🛠️ Tech Stack

| Layer           | Technology                        |
|-----------------|-----------------------------------|
| Frontend        | React.js                          |
| Backend         | Django + Django REST Framework    |
| LLM Services    | LLaMA 3.2 1B (customizable)       |
| Crawler         | Selenium                          |
| Scheduler       | Celery (2 workers + 1 beat)       |
| Message Queue   | Redis                             |
| Database        | PostgreSQL                        |
| Deployment      | Docker + Docker Compose           |

---

## 🚀 Installation & Setup

### ✅ Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Access to Meta Llama 3.2 1B model weights (request at [https://www.llama.com/llama-downloads](https://www.llama.com/llama-downloads) or Hugging Face). Users must comply with the Llama 3.2 Community License (see [License](#-license)).
- (Optional for development):
  - [Node.js](https://nodejs.org/) (v16+ recommended)
  - [Python](https://www.python.org/) (3.10+)
  - [pip](https://pip.pypa.io/en/stable/)
  - [npm](https://www.npmjs.com/)

### ⚡ Spin Up All Services

The project is fully dockerized. To build and start all services (backend, frontend, database, Redis, Celery workers), run:

```bash
docker-compose up --build
```

This command will:

- Build Docker images if not available
- Launch backend (Django) and frontend (React) containers
- Start PostgreSQL and Redis services
- Run Celery workers and beat scheduler

---

## 🗂️ Project Structure

```plaintext
newSumma/
├── backend/                  # Django backend project
│   ├── apps/                 # Django apps (crawler, summarizer, recommender, user, etc.)
│   ├── backend/              # Django settings and configuration
│   ├── manage.py             # Django management script
│   ├── Dockerfile            # Dockerfile for Django backend
│   └── requirements.txt      # Backend dependencies
├── frontend/                 # React frontend project
│   ├── public/               # Public assets
│   ├── src/                  # React source code
│   ├── package.json          # Frontend dependencies
│   ├── package-lock.json     # Locked frontend dependencies
│   └── Dockerfile            # Dockerfile for React frontend
├── .env                      # Environment variables for local development
├── docker-compose.yml        # Docker Compose configuration for all services
└── README.md                 # Project documentation
```

### Notes:

- The `.env` file contains sensitive environment variables (e.g., database credentials, API keys). Create it based on the provided `.env-example` file in the root directory.
- The `docker-compose.yml` file orchestrates all containers and is located in the root directory.
- Frontend dependencies are managed in `frontend/package.json` and `frontend/package-lock.json`.
- Backend dependencies are listed in `backend/requirements.txt`.

---

## ⚙️ Configuration

### Environment Variables (`.env`)

Create a `.env` file in the root directory by copying `.env-example` and updating it with your credentials.

Ensure all placeholders are replaced with actual values before running the project.

---

## 🧑‍💻 Author

**Kkrommm24**

---

## 📞 Contact

For questions or support, please open an issue on the [project repository](https://github.com/Kkrommm24/newSumma) or contact Kkrommm24 via email at [kkrommm24@example.com](mailto:kkrommm24@example.com).

---

## 📜 License

The source code of **newSumma** (e.g., Django backend, React frontend, and other custom components) is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### LLaMA 3.2 Usage

The news summarization component of **newSumma** is built with Meta Llama 3.2, which is licensed under the **Llama 3.2 Community License** (Copyright © Meta Platforms, Inc.). Key terms include:

- **Attribution**: This project is “Built with Llama” as required by the license.
- **Usage Restrictions**: LLaMA 3.2 is subject to the Acceptable Use Policy, prohibiting uses such as military applications or illegal activities. Organizations with over 700 million monthly active users must request a separate license from Meta.
- **EU Restriction**: Multimodal LLaMA 3.2 models (11B and 90B) are not licensed for use by individuals or companies based in the European Union, though end users of products incorporating these models are exempt.

The Llama 3.2 Community License is available at [https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE). Users must independently obtain access to LLaMA 3.2 model weights (e.g., via [https://www.llama.com/llama-downloads](https://www.llama.com/llama-downloads) or Hugging Face) and comply with its license terms.

---

Thank you for using **newSumma**! 🚀
