# ExpenseTracker

A modern, feature-rich expense tracking application built with Django and React.

## Features

- 📊 Dashboard with expense analytics and visualizations
- 💰 Track expenses and income
- 📱 Mobile-friendly responsive design
- 🔐 Secure authentication with JWT and social login
- 📈 Budget planning and tracking
- 📅 Monthly and yearly reports
- 🔔 Smart notifications and alerts
- 🌐 RESTful API
- 🔄 Real-time updates with Celery
- 🎨 Beautiful UI with Bootstrap 5

## Tech Stack

- **Backend**: Django 5.0, Django REST Framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **Authentication**: JWT, Social Auth (Google)
- **Frontend**: Bootstrap 5, FontAwesome
- **API**: RESTful API with JWT authentication

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14
- Redis
- Homebrew (for macOS)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/expense-tracker.git
   cd expense-tracker
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

4. Start the development server:
   ```bash
   python manage.py runserver
   ```

5. Start Celery worker (in a new terminal):
   ```bash
   celery -A budget_tracking worker -l info
   ```

6. Start Celery beat (in a new terminal):
   ```bash
   celery -A budget_tracking beat -l info
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - Login with JWT
- `POST /api/auth/google/login/` - Login with Google
- `POST /api/token/refresh/` - Refresh JWT token

### Expenses
- `GET /api/expenses/` - List expenses
- `POST /api/expenses/` - Create expense
- `GET /api/expenses/{id}/` - Get expense details
- `PUT /api/expenses/{id}/` - Update expense
- `DELETE /api/expenses/{id}/` - Delete expense

### Categories
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category
- `GET /api/categories/{id}/` - Get category details
- `PUT /api/categories/{id}/` - Update category
- `DELETE /api/categories/{id}/` - Delete category

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@expensetracker.com or open an issue in the repository.
