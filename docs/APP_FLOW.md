# DukaanFlow --- Application Flow

## 1. Primary Navigation

Desktop sidebar: 1. Overview 2. Customers / Khata 3. Suppliers 4.
Transactions 5. Cash Flow 6. What-If Simulator 7. Settings

Mobile bottom navigation: - Overview - Khata - Cash Flow - Simulator -
More

## 2. First Visit / Demo Flow

1.  User enters the demo workspace or signs in.
2.  App loads the selected business context.
3.  Dashboard shows available cash, receivables, payables, recent
    activity, upcoming items, and forecast summary.
4.  A visible demo-data label indicates that figures are illustrative.

## 3. Customer Flow

1.  Open Customers.
2.  Search/select a customer or add one.
3.  View outstanding balance and ledger history.
4.  Add a credit sale with amount and due date.
5.  Add repayment with amount/date/method.
6.  Backend validates amount and records the ledger event.
7.  Customer balance and relevant cash position/forecast refresh.

## 4. Supplier Flow

1.  Open Suppliers.
2.  Select or create supplier.
3.  Add bill, amount, bill date, and due date.
4.  View outstanding bill.
5.  Record partial/full payment.
6.  Bill status and cash position update.
7.  Forecast refreshes.

## 5. Expense Flow

1.  Open Transactions or Expenses.
2.  Enter title, category, amount, date, payment status, and method.
3.  If paid, record a cash outflow; if unpaid/planned, track the
    obligation separately.
4.  Forecast includes only future eligible outflows not already
    reflected in opening cash.

## 6. Forecast Flow

1.  Open Cash Flow.
2.  Backend builds eligible future events.
3.  Deterministic engine calculates daily closing balances.
4.  UI displays projected balance trajectory, inflow/outflow totals,
    safety buffer, and warnings.
5.  User opens an alert to see contributing events.

## 7. What-If Flow

1.  Open Simulator.
2.  Select a supported future event or add a hypothetical event.
3.  Change amount/date or add a planned expense.
4.  Backend calculates baseline and scenario using the same engine.
5.  UI compares daily balances, minimum balance, and shortage status.
6.  User can reset or save scenario.
7.  Actual ledger remains unchanged unless the user separately performs
    a real ledger action.

## 8. Error and Empty States

-   No customers: explain how to add the first customer.
-   No forecast events: show current cash and explain that the
    projection is based on recorded items.
-   Invalid repayment: explain the outstanding limit.
-   Failed API: preserve form data where safe and offer retry.
-   Stale data: show refresh state and avoid presenting old values as
    current.

## 9. Business Management (Phase 2)

1. Open Business Management to create a repayment schedule against a customer's unallocated outstanding credit.
2. Record full or partial instalment payments; each recorded payment is posted once to the customer ledger and cashbook.
3. Review overdue instalments, expense budgets, threshold alerts, and date-filtered reports.
4. Acknowledge due-soon and overdue customer/supplier reminders in-app. No WhatsApp or SMS is sent.
5. Dashboard surfaces next scheduled instalments, overdue plan count, and budget alert count. Forecast substitutes allocated debt collections with scheduled instalment dates and labels them estimates.
