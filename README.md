# Complaints Project

A microservices-based system to capture complaints from a web frontend, process them via Kafka, store in PostgreSQL, and send email notifications with optional file attachments.

---

## Architecture Diagram

```
[Frontend: React/Angular]
        |
        v
[Producer Service: FastAPI] --- publishes ---> [Kafka Topic: complaints.v1]
        |                                              |
        |                                              v
        |                                   [Consumer Service: FastAPI]
        |                                              |
        |                                +-------------+-------------+
        |                                |                           |
        v                                v                           v
   [PostgreSQL DB]             [Gmail SMTP: Send Email]       [Attachment Handling]

```

---

## Architecture

- **Frontend**: React/Angular app with a form to submit complaints (supports optional file upload).  
- **Producer Service**: FastAPI app that receives complaints and attachments, converts files to base64, and publishes JSON to Kafka.  
- **Kafka**: Message broker carrying complaint events and file data.  
- **Consumer Service**: FastAPI app that consumes from Kafka, saves complaint details in PostgreSQL, and sends email notifications with attachments.  
- **PostgreSQL**: Stores complaints and metadata.  
- **Gmail SMTP**: Sends user-facing complaint confirmation emails with attachments.  

---

## Prerequisites

- Docker & Docker Compose  
- Python 3.11+  
- Node.js 18+ (for React/Angular frontend)  
- Gmail account (App Password for SMTP)  

---

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd complaints-project
   ```

2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   ```

   Update `.env` with your local settings:

   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_EMAIL=your-email@gmail.com
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password   # Gmail App Password
   SMTP_STARTTLS=true
   ```

3. Start services with Docker Compose:
   ```bash
   docker-compose up --build
   ```

---

## Services

- **Producer API**: [http://localhost:8000/docs](http://localhost:8000/docs)  
- **Consumer API**: [http://localhost:8001/docs](http://localhost:8001/docs)  
- **Frontend (React/Angular)**: [http://localhost:3000](http://localhost:3000)  

---

## Workflow

1. User submits a complaint (with optional file) via the frontend.  
2. Producer service base64-encodes the file, wraps it in JSON, and publishes to Kafka topic `complaints.v1`.  
3. Consumer service consumes the event:  
   - Decodes base64 back to raw bytes.  
   - Saves complaint + metadata into PostgreSQL.  
   - Sends email notification via Gmail SMTP, attaching the decoded file if present.  

---

## Development

- To run producer service locally:
  ```bash
  cd producer
  uvicorn main:app --reload --port 8000
  ```

- To run consumer service locally:
  ```bash
  cd consumer
  uvicorn main:app --reload --port 8001
  ```

- To run frontend locally:
  ```bash
  cd frontend
  npm install
  npm start
  ```

---

## Testing

- Unit tests are in each service’s `tests/` directory.  
- Run tests with:
  ```bash
  pytest
  ```

---

## Notes

- Files are transferred **as-is** through Kafka, but base64-encoded to fit safely in JSON.  
- Gmail SMTP requires an **App Password** (not your regular Gmail password).  
- Large file uploads are not supported.  

---
