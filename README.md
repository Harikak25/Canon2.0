   [Frontend (Angular)]
              |
              v
     ┌───────────────────┐
     │   Producer API    │   (FastAPI)
     └───────────────────┘
              |
      writes complaint
              v
     ┌───────────────────┐
     │    PostgreSQL     │   (stores complaints)
     └───────────────────┘
              |
    publishes ID + meta
              v
     ┌───────────────────┐
     │      Kafka        │   (complaints.v1 topic)
     └───────────────────┘
              |
    consumes messages
              v
     ┌───────────────────┐
     │   Consumer API    │   (FastAPI)
     └───────────────────┘
              |
    triggers email sending
              v
     ┌───────────────────┐
     │    Gmail SMTP     │   (recipient inbox)
     └───────────────────┘
