# Construction Labour Management System

## Site lifecycle

- A site has an `active` or `closed` status. Closing is reversible; never delete a site because its historical attendance and financial records must remain available.
- The Today workflow requests active sites only, so closed sites do not appear for daily attendance.
- The backend must reject a new labourer assignment to a closed site. Historical boards and reports for closed sites remain readable.
- Sites can be reopened when work resumes.

## Site finances

- `contract_amount` is the optional amount agreed with the client for a site. It is not a client payment.
- Record every amount received from the client as a separate, append-only `site_client_receipts` record with amount, received date, note, creator, and timestamp. Do not overwrite a previous receipt to represent a new payment.
- The site finance summary shows:
  - agreed client amount;
  - total client receipts;
  - accrued labour cost from daily-work-record amounts;
  - travel expenses attached to those work records;
  - standalone site costs such as labour food;
  - total cost (`labour + travel + site costs`);
  - remaining amount due from the client when a contract amount exists.
- Profit is calculated from recorded costs only: `current_profit = client receipts - total cost`. When a contract amount exists, also show `expected_profit = contract amount - total cost`. Either can be negative and must be presented as a loss, not a positive profit.
- Do not add labourer settlement payments to the project cost summary: settlements pay the wages/travel already accrued and would double-count the same cost. Advances and deductions need explicit future rules before being added to this summary.
- Daily site costs such as labour food are append-only `site_expenses` records. Store their date, category (`FOOD` or `OTHER`), amount, optional note, and audit metadata. They are included once in total cost and profit.
- Financial writes require an authenticated admin and an audit-log entry. Use Decimal/Decimal128 monetary values; never float arithmetic.

## Relevant endpoints

- `POST /sites/{site_id}/close` and `POST /sites/{site_id}/reopen`
- `GET /sites/{site_id}/financial-summary`
- `GET /sites/{site_id}/client-receipts`
- `POST /sites/{site_id}/client-receipts`
- `GET /sites/{site_id}/expenses`
- `POST /sites/{site_id}/expenses`

## Payment breakdown

- A payment preview must show wages and petrol/travel expenses separately, plus their combined total earnings.
- Prior balance is the unpaid remainder (or overpayment) carried from earlier payment records.
- Adjustments are separate, unsettled correction ledger entries generated after a paid attendance or expense record changes. Show their reasons and signed amounts before a payment is recorded.

## Session refresh

- Access-token cookies are short-lived. On a 401 from a protected API request, the frontend calls `POST /auth/refresh` once, using the HttpOnly refresh cookie, then retries the original request.
- Concurrent expired requests share the same refresh call. If refresh fails or expires, the frontend returns the user to the login screen rather than repeatedly issuing unauthorized requests.
