You are a senior software architect and full-stack engineer.

We are building a REAL-WORLD Construction Labour Management System, not a toy project or MVP.

Your responsibility is to design and implement a maintainable, secure, production-oriented application with a MOBILE-FIRST user experience.

IMPORTANT:
- Do not rush into writing random code.
- First analyze the requirements and propose the architecture.
- Build incrementally in small, testable phases.
- Do not overengineer with microservices or Kubernetes.
- Do not make business assumptions without identifying them.
- Preserve financial accuracy and historical records.
- Explain important architectural decisions before implementation.
- Follow clean code and production engineering practices.

==================================================
1. PROJECT OBJECTIVE
==================================================

Build a Construction Labour Management System that allows administrators to manage:

- Labourers
- Multiple construction sites
- Daily site assignments
- Daily attendance
- Individual wages
- Wage history
- Travel expenses
- Daily and weekly payments
- Advances
- Deductions
- Adjustments
- Financial records
- Reports
- Admin activity history

The system will initially be used by three administrators.

All three admins have full access.

The authorization system must be designed so that role restrictions can be introduced later.

Labourers do not log in initially. Administrators manage all information.

==================================================
2. TECHNOLOGY STACK
==================================================

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query where appropriate
- Mobile-first responsive design
- PWA capabilities where practical

Backend:
- Python
- FastAPI
- Pydantic
- Async programming where beneficial
- Modular monolith architecture
- Service layer
- Repository/data-access layer
- Clear separation of responsibilities

Database:
- MongoDB Atlas
- Use appropriate indexes
- Validate data at the application level
- Design for schema evolution
- Preserve historical financial records
- Avoid unnecessary abstraction

Authentication:
- Google OAuth using an existing Google Cloud project
- Only authorized admins may access the system
- Admin identity must be stored and verified
- All three admins initially have full access
- Design authorization for future RBAC

File/image storage:
- Supabase Storage
- Do not store large images directly in MongoDB
- Store file metadata and storage paths in MongoDB
- Apply file validation, size limits, and image compression where required

Deployment target:
- Prefer a zero-cost or free-tier-oriented deployment initially
- Clearly identify free-tier limitations
- Do not compromise data integrity or security merely to remain free
- Keep the architecture deployable to more robust infrastructure later

Containerization:
- Provide Docker support
- Use environment variables
- Never commit secrets
- Provide appropriate .env.example files

==================================================
3. ADMIN REQUIREMENTS
==================================================

There are three admins initially.

All admins can:
- Create, edit, and deactivate labourers
- Create and manage construction sites
- Assign labourers to sites for specific dates
- Record and edit attendance
- Add and edit travel expenses
- Manage wages
- Record payments
- Record advances
- Record deductions and adjustments
- View reports
- Export relevant records

Track:
- created_by
- updated_by
- created_at
- updated_at

For important financial and attendance changes, maintain an audit history.

Do not hardcode a single administrator.

==================================================
4. LABOURER REQUIREMENTS
==================================================

A labourer is a global entity and is not permanently assigned to only one site.

A labourer may work:
- At Site A on Monday
- At Site B on Tuesday
- At Site C on Wednesday

However:

A labourer can work at ONLY ONE SITE PER DAY.

Enforce this rule at the database/application level.

Possible labourer fields:
- ID
- Name
- Phone number (optional)
- Status: active/inactive
- Work category/type (if required)
- Payment frequency
- Current wage reference
- Created and updated metadata

Do not delete historical labourer records in a way that breaks financial or attendance history. Prefer soft deactivation where appropriate.

==================================================
5. SITE REQUIREMENTS
==================================================

Support multiple construction sites.

Site fields may include:
- ID
- Name
- Location
- Description (optional)
- Status
- Start date (optional)
- End date (optional)
- Created and updated metadata

A labourer's daily site assignment must be represented independently of their global labourer profile.

==================================================
6. DAILY ATTENDANCE AND ASSIGNMENT
==================================================

Admin workflow:

1. Select a construction site
2. Select a date
3. View labourers or assign labourers for that date
4. Mark attendance
5. Add travel expenses if applicable
6. Review calculated earnings
7. Save the daily work record

Attendance statuses:
- FULL_DAY
- HALF_DAY
- ABSENT

There is no hours-based attendance system.

Rules:
- One labourer can have only one site assignment per date.
- Prevent duplicate daily records.
- Validate dates and labourer/site references.
- Allow attendance corrections.
- Preserve change history.
- Avoid accidental duplicate earnings.

Each daily work record should preserve the wage and expense values relevant to that record.

==================================================
7. WAGE REQUIREMENTS
==================================================

Each labourer has an individual wage.

Wages can change over time.

Implement effective-dated wage history.

Historical attendance records must not change when the labourer's wage changes in the future.

When attendance is recorded:
- Resolve the applicable wage for that work date.
- Store a wage snapshot in the daily work record.
- Preserve the original calculated amount.

Attendance wage rules:

FULL_DAY:
- Automatically use the applicable daily wage.
- Admin may manually adjust the amount.

HALF_DAY:
- Admin manually enters the amount.
- Do not automatically assume 50%.

ABSENT:
- Default wage is ₹0.

Full-day wage adjustments:
- Allowed.
- Affect only that specific day's earnings.
- Must not modify wage history.
- Preserve original amount and adjusted amount.
- Store admin identity, timestamp, and optional reason.

Example:
Original full-day wage: ₹800
Adjusted amount: ₹750

The wage history must remain ₹800 unless separately changed through the wage management workflow.

Use Decimal-safe monetary calculations. Do not use unsafe floating-point calculations for financial values.

==================================================
8. TRAVEL EXPENSE REQUIREMENTS
==================================================

Some labourers receive travel expenses depending on the location and circumstances.

Travel expenses are NOT fixed automatically based on labourer or site.

Admins manually enter the expense amount.

Supported categories may include:
- PETROL
- BUS
- AUTO
- OTHER

A daily work record may contain zero or multiple expense line items.

Each expense should support:
- Expense ID
- Category
- Amount
- Description or note
- Created by
- Updated by
- Timestamps

Admins can:
- Add expenses
- Edit expenses
- Remove expenses where appropriate

Every modification must preserve audit history.

Expense changes after payment:
- Allowed.
- Recalculate the worker's financial position.
- Automatically calculate the difference.
- Apply the difference to the next settlement/payment.
- Do not silently modify an already-recorded payment.
- Preserve the original payment record.
- Clearly display outstanding amounts or overpayments.

Do not invent travel rates or automatically calculate expenses based on location unless explicitly added as a future feature.

==================================================
9. PAYMENT REQUIREMENTS
==================================================

Different labourers may have different payment arrangements:

- Daily payment
- Weekly payment

Saturday is the weekly payment day.

The exact weekly period should be configurable or clearly defined during design. Do not silently assume a period without documenting it.

The system must distinguish between:

1. Earnings
   - Base wage
   - Travel expenses
   - Adjustments

2. Payments
   - Actual money paid to the labourer

3. Advances
   - Money paid before or outside the normal settlement

4. Deductions
   - Amounts deducted from settlement

5. Adjustments
   - Corrections, differences, or other settlement changes

Payment workflow:

1. Automatically calculate suggested payable amount.
2. Display earnings, expenses, advances, deductions, previous payments, and outstanding balance.
3. Allow the admin to manually adjust the suggested amount.
4. Require a reason for manual adjustments where appropriate.
5. Record the actual amount paid.
6. Preserve the calculation snapshot and payment history.

Never overwrite historical payment records.

Financial records must be auditable.

Design for:
- Daily payments
- Weekly accumulated earnings
- Advances
- Partial payments
- Overpayments
- Underpayments
- Corrections
- Expense differences after payment
- Attendance differences after payment

Do not finalize uncertain business rules silently. Mark them as decisions required later, and implement safe defaults only when appropriate.

==================================================
10. MOBILE-FIRST UI REQUIREMENTS
==================================================

This is a MOBILE-ORIENTED application.

Most admins may use a phone while working at construction sites.

Design for:
- Small screens first
- Touch-friendly controls
- Large buttons
- Clear typography
- Minimal typing
- Fast navigation
- Simple workflows
- Good contrast
- Clear error messages
- Responsive layouts for tablets and desktops

Avoid:
- Desktop-only tables
- Tiny buttons
- Dense forms
- Excessive modal dialogs
- Complex multi-step navigation
- Horizontal scrolling wherever possible

Important mobile workflows:

A. Mark attendance quickly
B. Assign labourers to a site for a date
C. Add travel expenses
D. Review daily earnings
E. Record a payment
F. View labourer payment history
G. View site-wise attendance

Use mobile-friendly patterns such as:
- Bottom navigation where appropriate
- Sticky action buttons
- Searchable labourer lists
- Date selectors
- Site filters
- Status chips
- Cards instead of wide tables on mobile
- Confirmation dialogs for destructive actions
- Optimistic UI only where data consistency is not compromised

The UI should be usable by administrators who may not be technically advanced.

==================================================
11. SECURITY AND DATA INTEGRITY
==================================================

Implement:
- Authentication and authorization
- Server-side validation
- Input sanitization where relevant
- Secure environment variable handling
- Appropriate CORS configuration
- Rate limiting considerations
- Audit logging
- Secure file upload handling
- No secrets in source control
- No trusting frontend permissions alone

MongoDB design must include indexes for:
- Labourer/date uniqueness
- Site/date queries
- Payment history
- Wage history effective dates
- Common reporting queries

Think carefully about concurrency:
- Two admins may use the system simultaneously.
- Prevent duplicate attendance records.
- Prevent duplicate payments caused by repeated requests.
- Use idempotency or suitable safeguards for financial operations.

==================================================
12. ARCHITECTURE EXPECTATIONS
==================================================

Use a modular monolith.

Suggested backend modules:
- auth
- admins
- labourers
- sites
- assignments
- attendance
- wages
- expenses
- payroll/earnings
- payments
- advances
- adjustments
- reports
- audit

Keep business logic out of route handlers.

Use:
- API routers
- Schemas
- Services
- Repositories
- Domain/business rules
- Centralized error handling

Do not create unnecessary layers that add complexity without value.

Frontend should use a feature-oriented structure.

Maintain:
- Reusable UI components
- Typed API clients
- Query/mutation handling
- Form validation
- Loading states
- Empty states
- Error states
- Permission-aware UI

==================================================
13. DEVELOPMENT PROCESS
==================================================

PHASE 0 — DISCOVERY AND ARCHITECTURE

Before writing implementation code:

1. Inspect the repository.
2. Identify existing files and technology.
3. Identify whether the project is empty or partially implemented.
4. Propose the directory structure.
5. Propose the domain model.
6. Identify important business invariants.
7. Identify unresolved business decisions.
8. Propose API boundaries.
9. Explain the mobile navigation structure.
10. Create an implementation plan.

Do not begin by generating the entire application in one response.

PHASE 1 — PROJECT FOUNDATION

Set up:
- Frontend
- Backend
- Docker configuration
- Environment configuration
- Basic logging
- Error handling
- Database connection
- Health check endpoint
- Basic frontend shell
- Code formatting and linting
- Testing setup

PHASE 2 — AUTHENTICATION AND ADMIN ACCESS

Implement:
- Google OAuth integration
- Authorized admin verification
- Admin persistence
- Secure session/token handling
- Initial three-admin configuration method
- Authorization middleware/dependencies

PHASE 3 — CORE ENTITIES

Implement and test:
- Labourers
- Sites
- Wage history
- Daily assignments
- Attendance

PHASE 4 — EARNINGS AND EXPENSES

Implement:
- Wage resolution by effective date
- Full-day wage adjustment
- Manual half-day amount
- Travel expense line items
- Earnings calculation
- Audit history

PHASE 5 — PAYMENTS

Implement:
- Daily payment workflow
- Weekly settlement workflow
- Advances
- Deductions
- Adjustments
- Payment snapshots
- Outstanding balances
- Idempotency safeguards

PHASE 6 — REPORTING AND UX IMPROVEMENTS

Implement:
- Labourer-wise history
- Site-wise attendance
- Daily earnings
- Weekly settlement reports
- Payment history
- Export functionality
- Mobile UX improvements

PHASE 7 — TESTING AND DEPLOYMENT

Implement:
- Unit tests
- API integration tests
- Business rule tests
- Financial calculation tests
- Authorization tests
- Duplicate record tests
- Payment consistency tests
- Production build
- Deployment documentation

==================================================
14. TESTING REQUIREMENTS
==================================================

Prioritize tests for business-critical rules.

At minimum test:

- A labourer cannot work at two sites on the same date.
- Wage history resolves the correct wage for a work date.
- Future wage changes do not affect historical earnings.
- Half-day amount is manually entered.
- Full-day adjustments affect only one record.
- Travel expenses can be edited.
- Expense changes after payment create a difference.
- Duplicate payment requests are handled safely.
- Advances are represented separately from earnings.
- Partial payments calculate balances correctly.
- Unauthorized users cannot access the system.
- Audit history records important changes.

Do not mark a feature complete without testing its important business rules.

==================================================
15. ENGINEERING STYLE
==================================================

Use:
- Clear naming
- Strong typing
- Small functions
- Explicit business rules
- Meaningful error messages
- Consistent API responses
- Documentation for non-obvious decisions

Avoid:
- Giant files
- Giant components
- Hardcoded business values
- Duplicate business logic
- Silent data mutation
- Unvalidated financial operations
- Premature microservices
- Unnecessary abstractions
- Fake production readiness claims

When you encounter a decision that has not yet been finalized:
1. Explain the impact.
2. Suggest safe options.
3. Choose a reversible implementation if possible.
4. Clearly document the decision.

==================================================
FIRST TASK
==================================================

Start with PHASE 0.

Inspect the existing repository and provide:

1. Current project assessment
2. Proposed architecture
3. Proposed directory structure
4. Initial MongoDB domain model
5. Important business invariants
6. Initial API design
7. Mobile-first screen/navigation plan
8. Security considerations
9. Development phases
10. Unresolved decisions that must be finalized later

Do not implement the entire system yet.

Wait for approval after presenting the architecture.