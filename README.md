# Library Management for ERPNext / Frappe

A focused library operations app for Frappe Framework. It helps librarians manage
articles, members, memberships, issuing, returns, overdue tracking, and fines from
a clean Desk workspace.

## Highlights

- Article catalog with availability status.
- Member and membership management.
- Issue and return workflow with validation.
- Automatic due dates based on library settings.
- Open, overdue, and returned transaction statuses.
- Overdue day calculation and configurable fine amount.
- Optional blocking when a member has overdue articles.
- Workspace dashboard with live number cards.
- Smart form buttons for faster issuing and returning.
- Colored list indicators for articles, transactions, and memberships.
- Daily scheduler hook to refresh overdue statuses.

## Desk Experience

The app adds a `Library Management` workspace with quick access to:

- Articles
- Library Members
- Library Memberships
- Library Transactions
- Library Settings

The workspace includes number cards for:

- Total Articles
- Available Articles
- Issued Articles
- Overdue Issues

## Core DocTypes

### Article

Stores catalog information such as article name, author, ISBN, publisher,
description, image, and availability status.

### Library Member

Stores member contact details and provides quick actions to create a membership,
issue an article, return an article, or view open transactions.

### Library Membership

Tracks active membership periods and payment status. The app prevents overlapping
submitted memberships for the same member.

### Library Transaction

Handles issue and return operations. Issue transactions store due dates and
status. Return transactions close the current open issue and make the article
available again.

### Library Setting

Controls operational rules:

- Loan Period
- Maximum Number of Issued Articles
- Fine Per Overdue Day
- Block Issue If Member Has Overdue Articles

## Business Rules

- An article cannot be issued if it already has an open issue.
- A return must be performed by the same member who issued the article.
- A member must have a valid submitted membership to issue an article.
- The maximum open issue limit is enforced per member.
- Overdue issues can block new issues when enabled in settings.
- Returned articles are automatically marked available.

## Installation

From your Frappe bench:

```bash
bench get-app https://github.com/Mohammed-Aljazzar/Library_management_erpnext.git
bench --site your-site.localhost install-app library_management
bench --site your-site.localhost migrate
bench --site your-site.localhost clear-cache
```

If you want the site to be served by default during local development:

```bash
bench use your-site.localhost
bench start
```

## Development

Install developer tooling:

```bash
cd apps/library_management
pre-commit install
```

Run migration after changing DocTypes, workspace, hooks, or number cards:

```bash
bench --site your-site.localhost migrate
bench --site your-site.localhost clear-cache
```

## Verification

Useful checks:

```bash
python3 -m py_compile library_management/library_management/doctype/library_transaction/library_transaction.py
python3 -m json.tool library_management/library_management/doctype/library_transaction/library_transaction.json
bench --site your-site.localhost list-apps
bench --site your-site.localhost migrate
```

The app includes tests for the library transaction workflow. Depending on your
Frappe environment, you may need to enable tests for the site before running
them:

```bash
bench --site your-site.localhost set-config allow_tests true
bench --site your-site.localhost run-tests --doctype "Library Transaction"
```

## Notes

This app intentionally keeps the first version simple by using `Article` as the
circulating item. A future version can split catalog titles from physical copies
with a dedicated `Book Copy` DocType for libraries that manage multiple copies of
the same title.

## License

MIT
