# Cloud-Based Inventory Management System

## 📌 Project Overview
A monolithic Flask web application built on a fully serverless Amazon Web Services (AWS) backend architecture. The system handles user authentication, product cataloging, inventory math, sales/purchase order processing, barcode scanning, and automated reporting.

## 🏗️ AWS Cloud Architecture & Services
The backend is completely decoupled from local infrastructure, leveraging AWS Free Tier services via the `boto3` SDK:

1. **Amazon DynamoDB (Database)**
   * **Role:** Primary NoSQL data store.
   * **Implementation:** Uses a composite partition key structure for `users`, `products`, and `orders`. Employs a custom Python query parser to translate complex filtering logic into Boto3 `scan` operations for fast pagination and barcode lookup.
2. **Amazon S3 (File Storage)**
   * **Role:** Stores product images and generated PDF reports.
   * **Implementation:** Automatically creates a unique bucket (`inventory-app-storage-<id>-<region>`). The bucket is configured with a Public Read policy to serve images directly to the frontend.
3. **Amazon SQS (Message Queues)**
   * **Role:** Asynchronous event queuing.
   * **Implementation:** Handles `inventory-updates`, `order-processing`, and `notifications` queues. Allows the web app to offload heavy tasks and respond to the user instantly.
4. **Amazon SES (Simple Email Service)**
   * **Role:** Transactional outbound emails.
   * **Implementation:** Sends system alerts (e.g., low-stock warnings) to verified Sandbox email addresses.
5. **AWS Lambda (Serverless Compute)**
   * **Role:** Background queue worker.
   * **Implementation:** A standalone script (`aws_lambdas/sqs_worker.py`) designed to be triggered by SQS. It consumes the messages and triggers SES emails or DynamoDB updates without requiring a 24/7 background server.
6. **Amazon CloudWatch (Monitoring)**
   * **Role:** Telemetry and logging.
   * **Implementation:** Uses standard Python logging (`monitor_service.py`), which AWS CloudWatch automatically ingests for free when deployed.

## ⚙️ Tech Stack
* **Frontend:** HTML, CSS, JavaScript (Vanilla), DataTables, Bootstrap.
* **Backend:** Python, Flask (Application Factory Pattern).
* **Cloud SDK:** `boto3` (AWS SDK for Python).
* **Security:** JWT (JSON Web Tokens) for API auth, Werkzeug password hashing.

## 📂 Core Project Structure
* `app/routes/`: Contains controllers for UI and REST APIs (`auth.py`, `products.py`, `orders.py`).
* `app/services/`: Singleton wrapper classes abstracting AWS integrations (`dynamodb_service.py`, `s3_service.py`, `sqs_service.py`, `ses_service.py`).
* `app/models/`: Data schemas and validation logic.
* `aws_lambdas/`: Serverless worker scripts for AWS Lambda deployment.

## 🚀 Environment Configuration
Requires a `.env` file in the root directory:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
ADMIN_EMAIL=your_verified_ses_email@gmail.com
SENDER_EMAIL=your_verified_ses_email@gmail.com
```

## 💡 Deployment Strategy
* **Web Server (Flask):** Deploy to **AWS Elastic Beanstalk** (Platform-as-a-Service). It auto-provisions a free `t2.micro` EC2 instance to host the website 24/7.
* **Background Worker:** Deploy `sqs_worker.py` to **AWS Lambda** (Serverless). It scales to zero and costs nothing when the system is idle.
