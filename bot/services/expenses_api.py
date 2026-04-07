
import httpx

from bot.config import settings


class ExpensesAPIClient:
    def __init__(self):
        self.base_url = settings.api_base_url
        self.headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        }

    async def create_expense(
        self,
        telegram_user_id: int,
        amount: float,
        category: str,
        description: str | None = None,
    ) -> dict | None:
        payload = {
            "telegram_user_id": telegram_user_id,
            "amount": str(amount),
            "category": category,
            "description": description,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/expenses/",
                json=payload,
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
            return None

    async def get_last_expense(self, telegram_user_id: int) -> dict | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/last/{telegram_user_id}",
                headers=self.headers,
            )
            if response.status_code == 200:
                data = response.json()
                return data if data else None
            return None

    async def delete_last_expense(self, telegram_user_id: int) -> dict | None:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/expenses/last/{telegram_user_id}",
                headers=self.headers,
            )
            if response.status_code == 200:
                data = response.json()
                return data if data else None
            return None

    async def get_today_expenses(
        self, telegram_user_id: int
    ) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/today/{telegram_user_id}",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
            return []

    async def get_total_today(self, telegram_user_id: int) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/total-today/{telegram_user_id}",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json().get("total", "0")
            return "0"

    async def get_expenses_by_date(
        self, telegram_user_id: int, target_date: str
    ) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/date/{telegram_user_id}/{target_date}",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
            return []

    async def get_expense_dates(self, telegram_user_id: int) -> list[str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/dates/{telegram_user_id}",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
            return []

    async def get_prev_expense_date(self, telegram_user_id: int, current_date: str) -> str | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/prev-date/{telegram_user_id}/{current_date}",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json().get("date")
            return None

    async def get_next_expense_date(self, telegram_user_id: int, current_date: str) -> str | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/expenses/next-date/{telegram_user_id}/{current_date}",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json().get("date")
            return None


api_client = ExpensesAPIClient()
