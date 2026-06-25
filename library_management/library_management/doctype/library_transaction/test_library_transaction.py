# Copyright (c) 2026, Faris Ansari and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, nowdate
from frappe.tests.utils import FrappeTestCase


class TestLibraryTransaction(FrappeTestCase):
	def setUp(self):
		frappe.db.set_single_value("Library Setting", "loan_period", 14)
		frappe.db.set_single_value("Library Setting", "maximum_number_of_issued_articles", 1)
		frappe.db.set_single_value("Library Setting", "fine_per_day", 2)
		frappe.db.set_single_value("Library Setting", "block_issue_if_overdue", 1)

	def create_article(self, title=None):
		title = title or f"Test Article {frappe.generate_hash(length=8)}"
		return frappe.get_doc(
			{
				"doctype": "Article",
				"article_name": title,
				"author": "Test Author",
				"status": "Available",
			}
		).insert()

	def create_member(self, first_name=None):
		member = frappe.get_doc(
			{
				"doctype": "Library Member",
				"first_name": first_name or f"Member {frappe.generate_hash(length=8)}",
				"last_name": "Test",
			}
		).insert()

		membership = frappe.get_doc(
			{
				"doctype": "Library Membership",
				"library_member": member.name,
				"from_date": add_days(nowdate(), -1),
				"paid": 1,
			}
		)
		membership.insert()
		membership.submit()

		return member

	def create_transaction(self, article, member, transaction_type):
		transaction = frappe.get_doc(
			{
				"doctype": "Library Transaction",
				"article": article.name,
				"library_member": member.name,
				"type": transaction_type,
				"date": nowdate(),
			}
		)
		transaction.insert()
		transaction.submit()
		return transaction

	def create_issue(self, article, member, due_date=None):
		transaction = frappe.get_doc(
			{
				"doctype": "Library Transaction",
				"article": article.name,
				"library_member": member.name,
				"type": "Issue",
				"date": nowdate(),
				"due_date": due_date,
			}
		)
		transaction.insert()
		transaction.submit()
		return transaction

	def test_issue_sets_due_date_and_return_reopens_limit(self):
		member = self.create_member()
		first_article = self.create_article()
		second_article = self.create_article()

		issue = self.create_transaction(first_article, member, "Issue")

		self.assertEqual(issue.due_date, add_days(nowdate(), 14))
		self.assertEqual(issue.status, "Open")
		self.assertEqual(frappe.db.get_value("Article", first_article.name, "status"), "Issued")

		with self.assertRaises(frappe.ValidationError):
			self.create_transaction(second_article, member, "Issue")

		self.create_transaction(first_article, member, "Return")

		self.assertEqual(frappe.db.get_value("Article", first_article.name, "status"), "Available")
		self.assertEqual(frappe.db.get_value("Library Transaction", issue.name, "status"), "Returned")
		self.create_transaction(second_article, member, "Issue")
		self.assertEqual(frappe.db.get_value("Article", second_article.name, "status"), "Issued")

	def test_return_must_be_by_issuing_member(self):
		issuing_member = self.create_member()
		other_member = self.create_member()
		article = self.create_article()

		self.create_transaction(article, issuing_member, "Issue")

		with self.assertRaises(frappe.ValidationError):
			self.create_transaction(article, other_member, "Return")

	def test_overdue_issue_blocks_new_issue_and_calculates_fine(self):
		member = self.create_member()
		overdue_article = self.create_article()
		next_article = self.create_article()

		issue = self.create_issue(overdue_article, member, due_date=add_days(nowdate(), -3))

		self.assertEqual(issue.status, "Overdue")
		self.assertEqual(issue.overdue_days, 3)

		with self.assertRaises(frappe.ValidationError):
			self.create_transaction(next_article, member, "Issue")

		return_transaction = self.create_transaction(overdue_article, member, "Return")

		self.assertEqual(return_transaction.overdue_days, 3)
		self.assertEqual(return_transaction.fine_amount, 6)
		self.assertEqual(frappe.db.get_value("Library Transaction", issue.name, "status"), "Returned")
