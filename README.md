💰 Finance Tracker & Budgeting App
A simple and intuitive web application for tracking personal finances and managing budgets, built with Streamlit and Python. This tool allows users to add transactions, automatically categorizes them using Google's Generative AI, and visualizes spending with a dashboard.

Features
Add Transactions: Easily log your income and expenses with a date, description, and amount.

AI-Powered Categorization: Transactions are automatically categorized (e.g., Food, Transport, Utilities) using Google's Generative AI, saving you time and effort.

Interactive Dashboard: Visualize your financial data with charts showing monthly spending trends and spending by category.

Monthly Budgeting: Set and track budgets for different spending categories to stay on top of your financial goals.

Transaction History: View, filter, and analyze all your past transactions in a clear, sortable table.

Getting Started
Prerequisites
To run this application, you need to have Python and a few libraries installed.

Python 3.8+

Google Generative AI API Key: You'll need an API key to enable the transaction categorization feature. You can get one from the Google AI for Developers website.

Installation
Clone the repository:

Bash

git clone <your-repository-url>
cd <your-repository-name>
Install the required Python packages:

Bash

pip install -r requirements.txt
Set up your API Key:
Create a file named secret.py in the root directory and add your API key:

Python

# secret.py
API_KEY = "YOUR_API_KEY"
Replace "YOUR_API_KEY" with the key you obtained from Google.

Running the App
After installation, you can launch the application with a single command:

Bash

streamlit run app.py
The app will open automatically in your default web browser at http://localhost:8503.

How to Use
Add Transactions: Use the input fields in the sidebar to enter the details of a new transaction. Click "Add Transaction" to save it. The app will automatically categorize it for you.

Set Budgets: In the sidebar, select a category and enter your desired monthly budget. This will be reflected in the "Budget vs. Actual Spending" table on the dashboard.

View Data: The app's main page is divided into two tabs:

Dashboard: Provides an overview of your spending with charts and budget comparisons.

Transaction History: Shows a detailed list of all your recorded transactions.