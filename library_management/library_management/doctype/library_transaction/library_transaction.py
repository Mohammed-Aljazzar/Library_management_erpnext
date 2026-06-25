import frappe
from frappe.model.document import Document
from frappe.model.docstatus import DocStatus
from frappe.utils import add_days, cint, date_diff, flt, nowdate


class LibraryTransaction(Document):
    def before_validate(self):
        self.date = self.date or nowdate()
        self.type = self.type or "Issue"

        if self.type == "Issue":
            loan_period = frappe.db.get_single_value("Library Setting", "loan_period") or 30
            self.due_date = self.due_date or add_days(self.date, loan_period)
            self.status = self.get_issue_status(self.due_date)
            self.overdue_days = self.get_overdue_days(self.due_date)
            self.fine_amount = 0
            self.returned_on = None
        elif self.type == "Return":
            open_issue = self.get_open_issue(self.article) if self.article else None
            self.returned_on = self.returned_on or self.date
            self.status = "Returned"
            self.overdue_days = self.get_overdue_days(open_issue.due_date) if open_issue else 0
            self.fine_amount = self.get_fine_amount(self.overdue_days)
            self.due_date = None

    def before_submit(self):
        if self.type == "Issue":
            self.validate_issue()
            self.validate_maximum_limit()
            self.validate_member_overdue_limit()
            frappe.db.set_value("Article", self.article, "status", "Issued")

        elif self.type == "Return":
            self.validate_return()
            self.close_open_issue()
            frappe.db.set_value("Article", self.article, "status", "Available")

    def on_cancel(self):
        self.update_article_status()

    def validate_issue(self):
        self.validate_membership()
        if self.get_open_issue(self.article):
            frappe.throw("Article is already issued by another member")

    def validate_return(self):
        open_issue = self.get_open_issue(self.article)
        if not open_issue:
            frappe.throw("Article cannot be returned without being issued first")

        if open_issue.library_member != self.library_member:
            frappe.throw("Article can only be returned by the member who issued it")

    def validate_maximum_limit(self):
        max_articles = frappe.db.get_single_value(
            "Library Setting", "maximum_number_of_issued_articles"
        )
        if max_articles and self.get_open_issue_count(self.library_member) >= max_articles:
            frappe.throw("Maximum limit reached for issuing articles")

    def validate_membership(self):
        # check if a valid membership exist for this library member
        valid_membership = frappe.db.exists(
            "Library Membership",
            {
                "library_member": self.library_member,
                "docstatus": DocStatus.submitted(),
                "from_date": ("<", self.date),
                "to_date": (">", self.date),
            },
        )
        if not valid_membership:
            frappe.throw("The member does not have a valid membership")

    def update_article_status(self):
        status = "Issued" if self.get_open_issue(self.article) else "Available"
        frappe.db.set_value("Article", self.article, "status", status)

    def close_open_issue(self):
        open_issue = self.get_open_issue(self.article)
        frappe.db.set_value(
            "Library Transaction",
            open_issue.name,
            {
                "status": "Returned",
                "returned_on": self.returned_on,
                "overdue_days": self.overdue_days,
                "fine_amount": self.fine_amount,
            },
        )

    @staticmethod
    def get_open_issue(article):
        issues = frappe.get_all(
            "Library Transaction",
            filters={
                "article": article,
                "type": "Issue",
                "docstatus": DocStatus.submitted(),
                "status": ("in", ["Open", "Overdue", ""]),
            },
            fields=["name", "library_member", "creation", "due_date", "status"],
            order_by="creation desc",
        )

        for issue in issues:
            has_return = frappe.db.exists(
                "Library Transaction",
                {
                    "article": article,
                    "type": "Return",
                    "library_member": issue.library_member,
                    "docstatus": DocStatus.submitted(),
                    "creation": (">", issue.creation),
                },
            )
            if not has_return:
                return issue

        return None

    @classmethod
    def get_open_issue_count(cls, library_member):
        articles = frappe.get_all(
            "Library Transaction",
            filters={
                "library_member": library_member,
                "type": "Issue",
                "docstatus": DocStatus.submitted(),
            },
            pluck="article",
            distinct=True,
        )

        return sum(
            1
            for article in articles
            if (open_issue := cls.get_open_issue(article))
            and open_issue.library_member == library_member
        )

    @staticmethod
    def get_overdue_days(due_date):
        if not due_date:
            return 0

        return max(date_diff(nowdate(), due_date), 0)

    @classmethod
    def get_issue_status(cls, due_date):
        return "Overdue" if cls.get_overdue_days(due_date) else "Open"

    @staticmethod
    def get_fine_amount(overdue_days):
        fine_per_day = frappe.db.get_single_value("Library Setting", "fine_per_day") or 0
        return flt(overdue_days) * flt(fine_per_day)

    @classmethod
    def get_member_overdue_count(cls, library_member):
        articles = frappe.get_all(
            "Library Transaction",
            filters={
                "library_member": library_member,
                "type": "Issue",
                "docstatus": DocStatus.submitted(),
            },
            pluck="article",
            distinct=True,
        )

        count = 0
        for article in articles:
            open_issue = cls.get_open_issue(article)
            if (
                open_issue
                and open_issue.library_member == library_member
                and cls.get_overdue_days(open_issue.due_date)
            ):
                count += 1

        return count

    def validate_member_overdue_limit(self):
        block_issue = cint(
            frappe.db.get_single_value("Library Setting", "block_issue_if_overdue")
        )
        if block_issue and self.get_member_overdue_count(self.library_member):
            frappe.throw("Member has overdue articles and cannot issue new articles")


def update_overdue_transactions():
    open_issues = frappe.get_all(
        "Library Transaction",
        filters={
            "type": "Issue",
            "docstatus": DocStatus.submitted(),
            "status": ("in", ["Open", "Overdue", ""]),
        },
        fields=["name", "article", "due_date"],
    )

    for issue in open_issues:
        status = LibraryTransaction.get_issue_status(issue.due_date)
        overdue_days = LibraryTransaction.get_overdue_days(issue.due_date)
        frappe.db.set_value(
            "Library Transaction",
            issue.name,
            {
                "status": status,
                "overdue_days": overdue_days,
                "fine_amount": LibraryTransaction.get_fine_amount(overdue_days),
            },
            update_modified=False,
        )


def sync_library_transaction_statuses():
    submitted_issues = frappe.get_all(
        "Library Transaction",
        filters={
            "type": "Issue",
            "docstatus": DocStatus.submitted(),
        },
        fields=["name", "article", "library_member", "creation", "due_date"],
        order_by="creation asc",
    )

    for issue in submitted_issues:
        has_return = frappe.db.exists(
            "Library Transaction",
            {
                "article": issue.article,
                "type": "Return",
                "library_member": issue.library_member,
                "docstatus": DocStatus.submitted(),
                "creation": (">", issue.creation),
            },
        )
        if has_return:
            overdue_days = LibraryTransaction.get_overdue_days(issue.due_date)
            values = {
                "status": "Returned",
                "overdue_days": overdue_days,
                "fine_amount": LibraryTransaction.get_fine_amount(overdue_days),
            }
        else:
            overdue_days = LibraryTransaction.get_overdue_days(issue.due_date)
            values = {
                "status": LibraryTransaction.get_issue_status(issue.due_date),
                "overdue_days": overdue_days,
                "fine_amount": LibraryTransaction.get_fine_amount(overdue_days),
            }

        frappe.db.set_value("Library Transaction", issue.name, values, update_modified=False)

    for article in frappe.get_all("Article", pluck="name"):
        status = "Issued" if LibraryTransaction.get_open_issue(article) else "Available"
        frappe.db.set_value("Article", article, "status", status, update_modified=False)


@frappe.whitelist()
def get_article_current_issue(article):
    open_issue = LibraryTransaction.get_open_issue(article)
    if not open_issue:
        return {}

    return {
        "transaction": open_issue.name,
        "library_member": open_issue.library_member,
        "due_date": open_issue.due_date,
        "status": LibraryTransaction.get_issue_status(open_issue.due_date),
        "overdue_days": LibraryTransaction.get_overdue_days(open_issue.due_date),
    }


@frappe.whitelist()
def get_member_summary(library_member):
    open_count = LibraryTransaction.get_open_issue_count(library_member)
    overdue_count = LibraryTransaction.get_member_overdue_count(library_member)

    open_issues = frappe.get_all(
        "Library Transaction",
        filters={
            "library_member": library_member,
            "type": "Issue",
            "docstatus": DocStatus.submitted(),
            "status": ("in", ["Open", "Overdue"]),
        },
        fields=["due_date"],
    )
    fine_amount = sum(
        LibraryTransaction.get_fine_amount(LibraryTransaction.get_overdue_days(issue.due_date))
        for issue in open_issues
    )

    return {
        "open_count": open_count,
        "overdue_count": overdue_count,
        "fine_amount": fine_amount,
    }
