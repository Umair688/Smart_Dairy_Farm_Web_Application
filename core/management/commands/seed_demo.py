"""Create a demo farm with 3 months of data so reports have something to show."""
import datetime as dt
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import get_profile
from animals.models import Animal
from core.utils import month_bounds, shift_month, today
from expenses.models import Expense
from income.models import Income
from milk.models import MilkRecord

DEMO_USER = "demo"
DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = "Create the demo user (demo / demo12345) with sample animals, milk, expenses and income."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete the demo user's data and recreate it.")

    def handle(self, *args, **options):
        User = get_user_model()
        if options["reset"]:
            User.objects.filter(username=DEMO_USER).delete()
        user, created = User.objects.get_or_create(username=DEMO_USER, defaults={"email": "demo@example.com"})
        if not created and Animal.objects.filter(owner=user).exists():
            self.stdout.write("Demo data already exists (use --reset to rebuild it).")
            return
        user.set_password(DEMO_PASSWORD)
        user.save()

        profile = get_profile(user)
        profile.farm_name = "Green Valley Dairy"
        profile.currency = "Rs"
        profile.default_milk_rate = Decimal("120.00")
        profile.save()

        rng = random.Random(42)
        herd = [
            ("C-01", "Laxmi", "cow", "Holstein Friesian", "lactating", 180000),
            ("C-02", "Gauri", "cow", "Holstein Friesian", "lactating", 170000),
            ("C-03", "Sundari", "cow", "Jersey", "lactating", 150000),
            ("B-01", "Nili", "buffalo", "Nili-Ravi", "lactating", 220000),
            ("B-02", "Kali", "buffalo", "Nili-Ravi", "lactating", 210000),
            ("C-04", "Rani", "cow", "Sahiwal", "dry", 140000),
            ("H-01", "Chanda", "cow", "Cross", "heifer", 0),
            ("K-01", "Moti", "calf", "Holstein Friesian", "heifer", 0),
        ]
        animals = {}
        for tag, name, kind, breed, status, price in herd:
            animals[tag] = Animal.objects.create(
                owner=user, tag_number=tag, name=name, animal_type=kind, breed=breed,
                status=status, purchase_price=Decimal(price),
                date_of_birth=today() - dt.timedelta(days=rng.randint(300, 2600)),
            )
        milkers = [a for a in animals.values() if a.status == "lactating"]
        base_liters = {"cow": 6.0, "buffalo": 5.5}

        t = today()
        milk_rows, expense_rows, income_rows = [], [], []
        for back in (2, 1, 0):  # two months ago, last month, this month
            year, month = shift_month(t.year, t.month, -back)
            first, last = month_bounds(year, month)
            end = min(last, t) if back == 0 else last
            day = first
            while day <= end:
                for animal in milkers:
                    for session, factor in (("morning", 1.0), ("evening", 0.85)):
                        liters = base_liters[animal.animal_type] * factor * rng.uniform(0.85, 1.15)
                        milk_rows.append(
                            MilkRecord(
                                owner=user, animal=animal, date=day, session=session,
                                liters=Decimal(f"{liters:.2f}"),
                                rate_per_liter=Decimal("120.00") if back else Decimal("125.00"),
                            )
                        )
                # Feed bought every few days
                if day.day % 4 == 1:
                    expense_rows.append(Expense(owner=user, date=day, category="feed",
                        amount=Decimal(rng.randint(9000, 12000)), description="Fodder and concentrate"))
                day += dt.timedelta(days=1)

            def add_expense(d, cat, amount, text):
                if d <= t:
                    expense_rows.append(Expense(owner=user, date=d, category=cat, amount=Decimal(amount), description=text))

            add_expense(first + dt.timedelta(days=1), "labour", 30000, "Monthly wages")
            add_expense(first + dt.timedelta(days=9), "electricity", rng.randint(5500, 7500), "Electricity and water")
            add_expense(first + dt.timedelta(days=11), "medicine", rng.randint(3000, 6000), "Medicines")
            add_expense(first + dt.timedelta(days=14), "vet", rng.randint(2500, 5000), "Vet visit and vaccination")
            if back == 2:  # one expensive month so the history shows a loss
                add_expense(first + dt.timedelta(days=5), "equipment", 85000, "New milking machine")
                add_expense(first + dt.timedelta(days=6), "vet", 18000, "Mastitis treatment")
            if back == 1 and first + dt.timedelta(days=12) <= t:
                income_rows.append(Income(owner=user, date=first + dt.timedelta(days=12), source="calf_sale",
                    amount=Decimal(45000), description="Male calf sold"))
            if first + dt.timedelta(days=19) <= t:
                income_rows.append(Income(owner=user, date=first + dt.timedelta(days=19), source="manure",
                    amount=Decimal(rng.randint(6000, 9000)), description="Manure sale"))

        MilkRecord.objects.bulk_create(milk_rows)
        Expense.objects.bulk_create(expense_rows)
        Income.objects.bulk_create(income_rows)
        self.stdout.write(self.style.SUCCESS(
            f"Demo farm ready: log in as '{DEMO_USER}' / '{DEMO_PASSWORD}' "
            f"({len(milk_rows)} milk, {len(expense_rows)} expense, {len(income_rows)} income records)."
        ))
