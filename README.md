
# E-Laundry Management System

![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Razorpay](https://img.shields.io/badge/Payment-Razorpay-blue?style=for-the-badge&logo=razorpay&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

---

## Introduction

Welcome to **E-Laundry**, a comprehensive laundry management solution designed to bridge the gap between customers, businesses, and logistics providers. Our platform simplifies the entire laundry process—from scheduling pickups to real-time order tracking and secure payments. 

Whether you are a busy professional needing a quick wash-and-fold service or a business managing bulk laundry needs, E-Laundry provides a seamless, efficient, and user-friendly experience. Built with robust technologies and a focus on reliability, we ensure your garments are handled with care and delivered on time. 

---

## Key Features

### For Users
*   **Easy Order Management**: Schedule pickups, track order status (Pending, Washing, Completed), and manage delivery preferences effortlessly.
*   **Subscription Plans**: Choose from flexible weekly or monthly subscription plans tailored to your needs.
*   **Secure Payments**: Integrated Razorpay gateway for safe and instant transactions.
*   **Real-time Tracking**: Monitor your laundry's journey from pickup to delivery.
*   **Bill Generation**: Detailed digital invoices for every order.

### For Businesses
*   **Bulk Order Handling**: Efficiently manage large-scale laundry requests.
*   **Customer Insights**: Access comprehensive profiles and order histories.
*   **Service Customization**: Define service types (Wash, Iron, Dry Clean) and manage specialized requests.

### For Logistics
*   **Delivery Management**: Assign and track delivery personnel for pickups and drop-offs.
*   **Route Optimization**: Streamline logistics operations with real-time status updates (Assigned, In Transit, Delivered).
*   **QR Code Integration**: Secure bag tracking using QR technology to prevent mix-ups.

### Admin Dashboard
*   **Centralized Control**: Oversee all users, businesses, orders, and payments from a single dashboard.
*   **Analytics**: Gain insights into daily orders, revenue, and service performance.

---

## Technology Stack

Our platform is built on a solid foundation of modern technologies to ensure performance, scalability, and security.

*   **Backend Framework**: Django (Python) - Robust, secure, and scalable.
*   **Frontend**: HTML5, Tailwind CSS, JavaScript - Responsive and modern UI.
*   **Database**: SQLite (Development) / MySQL (Production Ready).
*   **Payment Gateway**: Razorpay Integration.
*   **Task Scheduling**: Django-Crontab for automated tasks.

---

## Installation & Setup

Follow these steps to get the project up and running on your local machine.

### Prerequisites

Ensure you have the following installed:
*   Python 3.10 or higher
*   pip (Python package manager)
*   Virtualenv (recommended)

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/elaundry.git
    cd elaundry
    ```

2.  **Create and Activate Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Migrations**
    Apply the database migrations to set up the schema.
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create Superuser** (Admin Access)
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the Development Server**
    ```bash
    python manage.py runserver
    ```

    Access the application at `http://127.0.0.1:8000/`.

---

## Configuration

To enable payment features, you need to configure your Razorpay keys in `settings.py` or a `.env` file.

**Update `elaundry/settings.py`:**

```python
# Razorpay Configuration
RAZORPAY_KEY_ID = 'your_key_id_here'
RAZORPAY_KEY_SECRET = 'your_key_secret_here'
```

---

## Contribution

We welcome contributions! If you have suggestions or improvements, please fork the repository and create a pull request.

---


