"""Read-only tools exposed to the chat assistant.

TOOL_DISPATCH is the entire read-only guarantee: the model can only ever
invoke one of the async functions registered in that dict below. No
create/update/delete service method is referenced anywhere in this module,
and tools are declared to Gemini as explicit FunctionDeclaration schemas
(never as raw Python callables), so the SDK's automatic-function-calling /
reflection path never activates either. Keep it that way.
"""

from collections.abc import Awaitable, Callable
from datetime import date

from google.genai import types

from app.modules.adjustments.service import AdjustmentService
from app.modules.advances.service import AdvanceService
from app.modules.attendance.service import AttendanceService
from app.modules.deductions.service import DeductionService
from app.modules.labourers.service import LabourerService
from app.modules.payments.schemas import PeriodType
from app.modules.payments.service import PaymentService
from app.modules.reports.service import ReportService
from app.modules.sites.service import SiteService
from app.modules.wages.service import WageService

MAX_LIST_RESULTS = 50


def _truncate(items: list) -> tuple[list, int, bool]:
    total = len(items)
    truncated = total > MAX_LIST_RESULTS
    return items[:MAX_LIST_RESULTS], total, truncated


async def list_labourers(status: str | None = None, search: str | None = None) -> dict:
    results = await LabourerService().list(status=status, search=search)
    page, total, truncated = _truncate(results)
    return {
        "labourers": [r.model_dump(mode="json") for r in page],
        "total_count": total,
        "truncated": truncated,
    }


async def get_labourer(labourer_id: str) -> dict:
    return (await LabourerService().get(labourer_id)).model_dump(mode="json")


async def list_sites(status: str | None = None) -> dict:
    results = await SiteService().list(status=status)
    page, total, truncated = _truncate(results)
    return {
        "sites": [r.model_dump(mode="json") for r in page],
        "total_count": total,
        "truncated": truncated,
    }


async def get_site(site_id: str) -> dict:
    return (await SiteService().get(site_id)).model_dump(mode="json")


async def get_site_financial_summary(site_id: str) -> dict:
    return (await SiteService().financial_summary(site_id)).model_dump(mode="json")


async def get_site_crew_today(site_id: str, work_date: str | None = None) -> dict:
    work_day = date.fromisoformat(work_date) if work_date else date.today()
    board = await AttendanceService().get_board(site_id, work_day)
    return {"work_date": work_day.isoformat(), "entries": [b.model_dump(mode="json") for b in board]}


async def get_labourer_history(labourer_id: str, start_date: str, end_date: str) -> dict:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    report = await ReportService().labourer_history(labourer_id, start, end)
    return report.model_dump(mode="json")


async def get_site_attendance(site_id: str, start_date: str, end_date: str) -> dict:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    report = await ReportService().site_attendance(site_id, start, end)
    return report.model_dump(mode="json")


async def get_weekly_settlement(period_start: str, period_end: str) -> dict:
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    report = await ReportService().weekly_settlement(start, end)
    return report.model_dump(mode="json")


async def get_payment_preview(
    labourer_id: str, period_type: str, period_start: str, period_end: str
) -> dict:
    preview = await PaymentService().preview(
        labourer_id,
        PeriodType(period_type),
        date.fromisoformat(period_start),
        date.fromisoformat(period_end),
    )
    return preview.model_dump(mode="json")


async def get_labourer_ledger(labourer_id: str) -> dict:
    labourer = await LabourerService().get(labourer_id)
    wages = await WageService().list_history(labourer_id)
    advances = await AdvanceService().list_for_labourer(labourer_id)
    deductions = await DeductionService().list_for_labourer(labourer_id)
    adjustments = await AdjustmentService().list_for_labourer(labourer_id)
    payments = await PaymentService().list_for_labourer(labourer_id)
    return {
        "labourer_id": labourer_id,
        "labourer_name": labourer.name,
        "wage_history": [w.model_dump(mode="json") for w in wages],
        "advances": [a.model_dump(mode="json") for a in advances],
        "deductions": [d.model_dump(mode="json") for d in deductions],
        "adjustments": [a.model_dump(mode="json") for a in adjustments],
        "payments": [p.model_dump(mode="json") for p in payments],
    }


_RESOLVE_NAME_NOTE = (
    " Callers refer to people and sites by NAME, never by id -- if you only "
    "have a name, call list_labourers or list_sites first to resolve it to an id."
)

LIST_LABOURERS_DECLARATION = types.FunctionDeclaration(
    name="list_labourers",
    description=(
        "List labourers, optionally filtered by status and/or a free-text search "
        "on name or phone. Use this to resolve a labourer's name to their id. "
        "Results are capped at 50 -- narrow `search` for a specific person."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "status": types.Schema(
                type=types.Type.STRING,
                description="Filter by labourer status. Omit to include both.",
                enum=["active", "inactive"],
            ),
            "search": types.Schema(
                type=types.Type.STRING,
                description="Free-text match against labourer name or phone number.",
            ),
        },
    ),
)

GET_LABOURER_DECLARATION = types.FunctionDeclaration(
    name="get_labourer",
    description="Get a single labourer's profile (status, phone, category, etc.) by id."
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "labourer_id": types.Schema(type=types.Type.STRING, description="The labourer's database id.")
        },
        required=["labourer_id"],
    ),
)

LIST_SITES_DECLARATION = types.FunctionDeclaration(
    name="list_sites",
    description=(
        "List construction sites, optionally filtered by status. Use this to "
        "resolve a site's name to its id. Results are capped at 50."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "status": types.Schema(
                type=types.Type.STRING,
                description="Filter by site status. Omit to include both.",
                enum=["active", "closed"],
            ),
        },
    ),
)

GET_SITE_DECLARATION = types.FunctionDeclaration(
    name="get_site",
    description="Get a single site's profile (location, dates, contract amount) by id."
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={"site_id": types.Schema(type=types.Type.STRING, description="The site's database id.")},
        required=["site_id"],
    ),
)

GET_SITE_FINANCIAL_SUMMARY_DECLARATION = types.FunctionDeclaration(
    name="get_site_financial_summary",
    description=(
        "Get a site's financial summary: contract amount, client receipts, labour "
        "cost, travel expenses, site expenses, total cost, current profit, and "
        "expected profit."
    )
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={"site_id": types.Schema(type=types.Type.STRING, description="The site's database id.")},
        required=["site_id"],
    ),
)

GET_SITE_CREW_TODAY_DECLARATION = types.FunctionDeclaration(
    name="get_site_crew_today",
    description="Get the labourers assigned and/or marked present at a site on a given date."
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "site_id": types.Schema(type=types.Type.STRING, description="The site's database id."),
            "work_date": types.Schema(
                type=types.Type.STRING, description="YYYY-MM-DD. Omit to use today's date."
            ),
        },
        required=["site_id"],
    ),
)

GET_LABOURER_HISTORY_DECLARATION = types.FunctionDeclaration(
    name="get_labourer_history",
    description=(
        "Get a labourer's work records, payments, total earnings, and outstanding "
        "balance for a date range."
    )
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "labourer_id": types.Schema(type=types.Type.STRING, description="The labourer's database id."),
            "start_date": types.Schema(type=types.Type.STRING, description="Start of the period, YYYY-MM-DD."),
            "end_date": types.Schema(
                type=types.Type.STRING, description="End of the period, YYYY-MM-DD, inclusive."
            ),
        },
        required=["labourer_id", "start_date", "end_date"],
    ),
)

GET_SITE_ATTENDANCE_DECLARATION = types.FunctionDeclaration(
    name="get_site_attendance",
    description="Get every attendance entry and the total labour amount for a site over a date range."
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "site_id": types.Schema(type=types.Type.STRING, description="The site's database id."),
            "start_date": types.Schema(type=types.Type.STRING, description="Start of the period, YYYY-MM-DD."),
            "end_date": types.Schema(
                type=types.Type.STRING, description="End of the period, YYYY-MM-DD, inclusive."
            ),
        },
        required=["site_id", "start_date", "end_date"],
    ),
)

GET_WEEKLY_SETTLEMENT_DECLARATION = types.FunctionDeclaration(
    name="get_weekly_settlement",
    description=(
        "Get the suggested settlement amount for every active labourer over a "
        "period, and who still has unpaid earnings. No id needed -- covers all "
        "active labourers at once. Good for 'who is due this week' questions."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "period_start": types.Schema(type=types.Type.STRING, description="YYYY-MM-DD."),
            "period_end": types.Schema(type=types.Type.STRING, description="YYYY-MM-DD, inclusive."),
        },
        required=["period_start", "period_end"],
    ),
)

GET_PAYMENT_PREVIEW_DECLARATION = types.FunctionDeclaration(
    name="get_payment_preview",
    description=(
        "Preview what a labourer would be paid if settled right now for a period: "
        "wages, travel expenses, unsettled advances/deductions/adjustments, prior "
        "balance, and the suggested payout amount. This does NOT create a payment "
        "-- it is a read-only calculation, good for 'how much do we owe X' questions."
    )
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "labourer_id": types.Schema(type=types.Type.STRING, description="The labourer's database id."),
            "period_type": types.Schema(
                type=types.Type.STRING,
                description="Settlement period cadence.",
                enum=["daily", "weekly"],
            ),
            "period_start": types.Schema(type=types.Type.STRING, description="YYYY-MM-DD."),
            "period_end": types.Schema(type=types.Type.STRING, description="YYYY-MM-DD, inclusive."),
        },
        required=["labourer_id", "period_type", "period_start", "period_end"],
    ),
)

GET_LABOURER_LEDGER_DECLARATION = types.FunctionDeclaration(
    name="get_labourer_ledger",
    description=(
        "Get a labourer's full financial ledger in one call: wage history, "
        "advances, deductions, adjustments, and past payments. Good for 'what "
        "does X's account look like' or 'has X taken any advances' questions."
    )
    + _RESOLVE_NAME_NOTE,
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "labourer_id": types.Schema(type=types.Type.STRING, description="The labourer's database id.")
        },
        required=["labourer_id"],
    ),
)

TOOL_DECLARATIONS = types.Tool(
    function_declarations=[
        LIST_LABOURERS_DECLARATION,
        GET_LABOURER_DECLARATION,
        LIST_SITES_DECLARATION,
        GET_SITE_DECLARATION,
        GET_SITE_FINANCIAL_SUMMARY_DECLARATION,
        GET_SITE_CREW_TODAY_DECLARATION,
        GET_LABOURER_HISTORY_DECLARATION,
        GET_SITE_ATTENDANCE_DECLARATION,
        GET_WEEKLY_SETTLEMENT_DECLARATION,
        GET_PAYMENT_PREVIEW_DECLARATION,
        GET_LABOURER_LEDGER_DECLARATION,
    ]
)

# The single, fixed, hand-written allowlist -- structurally the only way the
# model can ever cause a database call. Never add anything here beyond the
# read-only wrappers defined above.
TOOL_DISPATCH: dict[str, Callable[..., Awaitable[dict]]] = {
    "list_labourers": list_labourers,
    "get_labourer": get_labourer,
    "list_sites": list_sites,
    "get_site": get_site,
    "get_site_financial_summary": get_site_financial_summary,
    "get_site_crew_today": get_site_crew_today,
    "get_labourer_history": get_labourer_history,
    "get_site_attendance": get_site_attendance,
    "get_weekly_settlement": get_weekly_settlement,
    "get_payment_preview": get_payment_preview,
    "get_labourer_ledger": get_labourer_ledger,
}
