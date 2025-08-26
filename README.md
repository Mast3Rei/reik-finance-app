# Reik Finance App
financial dashboard for personal budgeting 


A cloud‑native personal finance tracker designed to help users monitor spending, set budgets, and visualize financial trends in real time. Built with a modern, scalable stack and designed for seamless deployment.

## 🚀 Features
- **User Authentication & Security** – AWS Cognito OAuth integration for secure sign‑up/sign‑in.
- **Budget Tracking** – Create and manage monthly spending limits.
- **Transaction Management** – Add, edit, and categorize expenses.
- **Data Visualization** – Interactive charts for category breakdowns and spending trends.
- **Responsive UI** – Optimized for desktop.

## 🛠 Tech Stack
- **Frontend:** Svelte
- **Backend:** Django REST Framework
- **Cloud Services:** AWS Amplify, AWS Cognito
- **Database:** AWS DynamoDB
- **Deployment:** AWS ECS and Docker

## 📦 Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/Mast3Rei/reik-finance-app.git
   cd reik-finance-app

2. **Backend setup**
  cd backend
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver
4. **Frontend setup**
   cd frontend
  npm install
  npm run dev


## Environment Variables
  AWS_COGNITO_CLIENT_ID=your_client_id
  AWS_COGNITO_USER_POOL_ID=your_user_pool_id
  DATABASE_URL=your_database_url

## Screenshots
<img width="1913" height="818" alt="Screenshot 2025-08-25 221628" src="https://github.com/user-attachments/assets/bc8ce400-8dac-479f-b83e-c30912a6e4ab" />

<img width="1919" height="810" alt="Screenshot 2025-08-25 221704" src="https://github.com/user-attachments/assets/5d730d9f-160f-47c6-841a-67b12a80fcd3" />

  
