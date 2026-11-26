import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from animals.models import Animal
from expenses.models import Expense
from income.models import Income
from milk.models import MilkRecord
from reports.services import month_series, month_summary

User = get_user_model()


class AuthTests(TestCase):
    def test_register_creates_profile_and_logs_in(self):
        resp = self.client.post(
            reverse("accounts:register"),
            {
                "username": "farmer1", "email": "f1@example.com", "farm_name": "Test Farm",
                "password1": "S0me-strong-pass!", "password2": "S0me-strong-pass!",
            },
        )
        self.assertRedirects(resp, reverse("dashboard:home"))
        user = User.objects.get(username="farmer1")
        self.assertEqual(user.profile.farm_name, "Test Farm")
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 200)

    def test_login_and_logout(self):
        User.objects.create_user("u", "u@example.com", "pass12345!x")
        self.assertTrue(self.client.login(username="u", password="pass12345!x"))
        self.client.post(reverse("accounts:logout"))
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 302)

    def test_pages_require_login(self):
        for name in ("animals:list", "milk:list", "expenses:list", "income:list", "reports:monthly", "reports:yearly"):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, name)
            self.assertIn("/accounts/login/", resp["Location"])


class IsolationTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user("a", password="pass12345!x")
        self.b = User.objects.create_user("b", password="pass12345!x")
        self.animal_b = Animal.objects.create(owner=self.b, tag_number="X1", name="Bella")

    def test_user_cannot_see_or_edit_other_users_data(self):
        self.client.login(username="a", password="pass12345!x")
        self.assertNotContains(self.client.get(reverse("animals:list")), "Bella")
        self.assertEqual(self.client.get(reverse("animals:edit", args=[self.animal_b.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("animals:delete", args=[self.animal_b.pk])).status_code, 404)
        self.assertTrue(Animal.objects.filter(pk=self.animal_b.pk).exists())

    def test_cannot_attach_other_users_animal_to_a_record(self):
        self.client.login(username="a", password="pass12345!x")
        resp = self.client.post(
            reverse("milk:add"),
            {"date": "2026-11-01", "session": "morning", "animal": self.animal_b.pk,
             "liters": "5", "rate_per_liter": "100"},
        )
        self.assertEqual(resp.status_code, 200)  # form re-rendered with an error
        self.assertEqual(MilkRecord.objects.count(), 0)


class CrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("c", password="pass12345!x")
        self.client.login(username="c", password="pass12345!x")

    def test_full_crud_flow(self):
        r = self.client.post(reverse("animals:add"), {
            "tag_number": "T-1", "name": "Daisy", "animal_type": "cow", "status": "lactating", "purchase_price": "0"})
        self.assertRedirects(r, reverse("animals:list"))
        animal = Animal.objects.get(owner=self.user)
        # duplicate tag rejected
        r = self.client.post(reverse("animals:add"), {
            "tag_number": "t-1", "animal_type": "cow", "status": "dry", "purchase_price": "0"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Animal.objects.count(), 1)

        self.client.post(reverse("milk:add"), {"date": "2026-11-02", "session": "morning",
            "animal": animal.pk, "liters": "10.5", "rate_per_liter": "100"})
        self.client.post(reverse("expenses:add"), {"date": "2026-11-02", "category": "feed", "amount": "300"})
        self.client.post(reverse("income:add"), {"date": "2026-11-03", "source": "manure", "amount": "200"})
        for name in ("animals:list", "milk:list", "expenses:list", "income:list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("milk:list") + "?month=2026-11&choice=morning&q=T-1").status_code, 200)

        record = MilkRecord.objects.get()
        self.client.post(reverse("milk:edit", args=[record.pk]), {"date": "2026-11-02", "session": "evening",
            "animal": animal.pk, "liters": "11", "rate_per_liter": "100"})
        record.refresh_from_db()
        self.assertEqual(record.session, "evening")
        self.client.post(reverse("milk:delete", args=[record.pk]))
        self.assertEqual(MilkRecord.objects.count(), 0)


class ReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("r", password="pass12345!x")
        self.other = User.objects.create_user("o", password="pass12345!x")
        d = dt.date
        MilkRecord.objects.create(owner=self.user, date=d(2026, 10, 3), liters=Decimal("10"), rate_per_liter=Decimal("100"))
        MilkRecord.objects.create(owner=self.user, date=d(2026, 10, 4), liters=Decimal("20.5"), rate_per_liter=Decimal("100"))
        Income.objects.create(owner=self.user, date=d(2026, 10, 5), source="manure", amount=Decimal("500"))
        Expense.objects.create(owner=self.user, date=d(2026, 10, 6), category="feed", amount=Decimal("2000"))
        Expense.objects.create(owner=self.user, date=d(2026, 10, 7), category="vet", amount=Decimal("1000"))
        # outside the month and other user's data must not leak in
        Expense.objects.create(owner=self.user, date=d(2026, 11, 1), category="feed", amount=Decimal("999"))
        MilkRecord.objects.create(owner=self.other, date=d(2026, 10, 3), liters=Decimal("99"), rate_per_liter=Decimal("100"))

    def test_loss_month_math(self):
        s = month_summary(self.user, 2026, 10)
        self.assertEqual(s["milk_liters"], Decimal("30.50"))
        self.assertEqual(s["milk_revenue"], Decimal("3050.00"))
        self.assertEqual(s["other_income"], Decimal("500.00"))
        self.assertEqual(s["total_income"], Decimal("3550.00"))
        self.assertEqual(s["total_expense"], Decimal("3000.00"))
        self.assertEqual(s["net"], Decimal("550.00"))
        self.assertEqual(s["status"], "profit")
        self.assertEqual(s["expense_rows"][0]["key"], "feed")

    def test_loss_status_and_empty(self):
        Expense.objects.create(owner=self.user, date=dt.date(2026, 10, 8), category="equipment", amount=Decimal("5000"))
        s = month_summary(self.user, 2026, 10)
        self.assertEqual(s["status"], "loss")
        self.assertEqual(s["net"], Decimal("-4450.00"))
        self.assertEqual(month_summary(self.user, 2020, 1)["status"], "empty")

    def test_series_matches_summary(self):
        series = month_series(self.user, 2026, 11, 3)
        self.assertEqual([r["value"] for r in series], ["2026-09", "2026-10", "2026-11"])
        self.assertEqual(series[1]["net"], Decimal("550.00"))
        self.assertEqual(series[2]["net"], Decimal("-999.00"))

    def test_report_pages_and_exports(self):
        self.client.login(username="r", password="pass12345!x")
        resp = self.client.get(reverse("reports:monthly") + "?month=2026-10")
        self.assertContains(resp, "PROFIT")
        self.assertEqual(self.client.get(reverse("reports:monthly") + "?month=garbage").status_code, 200)
        self.assertEqual(self.client.get(reverse("reports:yearly") + "?year=2026").status_code, 200)
        csv_resp = self.client.get(reverse("reports:csv") + "?month=2026-10")
        self.assertEqual(csv_resp["Content-Type"], "text/csv")
        self.assertIn(b"Net profit / loss", csv_resp.content)
        pdf_resp = self.client.get(reverse("reports:pdf") + "?month=2026-10")
        self.assertEqual(pdf_resp["Content-Type"], "application/pdf")
        self.assertTrue(pdf_resp.content.startswith(b"%PDF"))
