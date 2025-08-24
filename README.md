<img width="602" height="650" alt="image" src="https://github.com/user-attachments/assets/2b8656ba-b90f-4ea8-9082-ecc3f60e5036" />




# Complaints Project

This project implements a simple **complaint management pipeline** using Angular, FastAPI, PostgreSQL, Kafka, and Gmail SMTP.  

It allows users to submit complaints through a frontend form, persist them in a database, publish complaint events to Kafka, and finally send email notifications through Gmail.

---

## Components

- **Frontend (Angular)** – Form to capture complaints.  
- **Producer API (FastAPI)** – Accepts complaints, stores them in PostgreSQL, and publishes events to Kafka.  
- **PostgreSQL** – Database to persist complaint records.  
- **Kafka** – Message broker (topic: `complaints.v1`) to decouple producer and consumer.  
- **Consumer API (FastAPI)** – Listens to Kafka events and triggers email notifications.  
- **SMTP (Gmail in prod / Mailhog in dev)** – Sends emails to recipients.  

---

## Running Locally

1. Clone the repo and navigate into it:
   ```bash
   git clone <repo-url>
   cd complaints-project
   ```

2. Start services with Docker:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
   ```

3. Access:
   - **Frontend (Angular):** `http://localhost:4200`  
   - **Producer API (Swagger):** `http://localhost:8000/docs`  
   - **Consumer API health:** `http://localhost:8001/health`  
   - **Mailhog (dev SMTP UI):** `http://localhost:8025`  

---

## Email Setup

For Gmail SMTP, add this to `.env.local`:

```env
SMTP_EMAIL=your@gmail.com
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=app-specific-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_STARTTLS=true
```

> ⚠️ Use an **App Password** for Gmail. Do not commit `.env.local` to source control.

---

## Testing

Run backend tests with coverage:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm producer pytest --cov=app --cov-report=html
docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm consumer pytest --cov=app --cov-report=html
```

Reports are available at `htmlcov/index.html`.

