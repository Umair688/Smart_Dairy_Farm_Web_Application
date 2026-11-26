# Smart Dairy Farm Management System

A simple, free web app for dairy farmers. Record your animals, daily milk, expenses and income,
and the app creates a **monthly profit and loss report** for you.

Built only with Django. No paid services and no API keys.

## Features

- **Register and login:** every farmer has their own account and sees only their own data
- **Dashboard:** milk today, this month's income, expenses and profit or loss, with a 6-month chart
- **Animals:** tag, name, type, breed, birth date, status and purchase price
- **Milk records:** morning and evening milk per animal or for the whole herd
- **Expenses:** feed, medicine, vet, labour, electricity, equipment and more
- **Income:** animal sales, manure and other income (milk sales are counted automatically)
- **Monthly report:** choose a month and see whether you made a profit or a loss
  - income and expense breakdowns
  - cost per liter and break-even milk price
  - top milk producers and charts
  - short, plain-language observations
  - export to **CSV** or **PDF**, or print
- **Yearly overview:** all 12 months side by side

## How profit and loss is calculated

```
Milk sales   = liters x rate per liter
Total income = Milk sales + Other income
Result       = Total income - Total expenses
```

A positive result is a profit. A negative result is a loss.

## Built with

- Python and Django
- SQLite (can be switched to PostgreSQL)
- Bootstrap 5 and Chart.js (included in the project, so it works offline)
- ReportLab for PDF reports

## How to run

1. Install Python 3.
2. Download or clone this project.
3. Open a terminal in the project folder and run:

```bash
python -m venv venv
venv\Scripts\activate          # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

4. Open http://127.0.0.1:8000 and click **Register** to create your account.

Optional: run `python manage.py seed_demo` to add sample farm data and see the reports filled in.

## Run the tests

```bash
python manage.py test
```

## Project structure

| Folder | Purpose |
|---|---|
| `accounts` | registration, login, farm profile |
| `dashboard` | home page |
| `animals`, `milk`, `expenses`, `income` | farm modules |
| `reports` | profit and loss calculation, charts, CSV and PDF |
| `core` | shared code, templates and styles |

## Configuration

Settings such as the secret key, debug mode and database are read from environment variables.
Never commit real secrets to the repository.

## License

Free to use and learn from. Add a license of your choice (for example MIT).