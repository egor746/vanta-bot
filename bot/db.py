import aiosqlite
from datetime import datetime, timedelta


class Database:
    def __init__(self, path: str = "gruzo.db"):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    role TEXT,
                    accepted_rules INTEGER DEFAULT 0,
                    registered_at TEXT,
                    premium_until TEXT,
                    rating REAL DEFAULT 5.0,
                    recommends INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dispatcher_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    address TEXT NOT NULL,
                    geo_lat REAL,
                    geo_lon REAL,
                    start_at TEXT NOT NULL,
                    workers_needed INTEGER NOT NULL,
                    workers_taken INTEGER DEFAULT 0,
                    rate_per_hour INTEGER NOT NULL,
                    hours INTEGER NOT NULL,
                    secure_object INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'open',
                    group_message_id INTEGER,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS order_workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    worker_id INTEGER NOT NULL,
                    UNIQUE(order_id, worker_id)
                );

                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    period_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT
                );
                """
            )
            await db.commit()

    async def upsert_user(self, user_id: int, username: str | None, full_name: str) -> None:
        now = datetime.utcnow().isoformat()
        premium_until = (datetime.utcnow() + timedelta(days=30)).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO users(user_id, username, full_name, registered_at, premium_until)
                VALUES(?,?,?,?,?)
                ON CONFLICT(user_id)
                DO UPDATE SET username=excluded.username, full_name=excluded.full_name
                """,
                (user_id, username, full_name, now, premium_until),
            )
            await db.commit()

    async def set_role_and_rules(self, user_id: int, role: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE users SET role=?, accepted_rules=1 WHERE user_id=?",
                (role, user_id),
            )
            await db.commit()

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            return await cur.fetchone()

    async def count_dispatcher_orders_current_month(self, user_id: int) -> int:
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT COUNT(*) FROM orders WHERE dispatcher_id=? AND created_at>=?",
                (user_id, month_start),
            )
            row = await cur.fetchone()
            return row[0]

    async def create_order(self, data: dict) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """
                INSERT INTO orders(
                    dispatcher_id, description, address, geo_lat, geo_lon, start_at,
                    workers_needed, rate_per_hour, hours, secure_object, created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    data["dispatcher_id"],
                    data["description"],
                    data["address"],
                    data.get("geo_lat"),
                    data.get("geo_lon"),
                    data["start_at"],
                    data["workers_needed"],
                    data["rate_per_hour"],
                    data["hours"],
                    int(data["secure_object"]),
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()
            return cur.lastrowid

    async def set_order_message_id(self, order_id: int, message_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE orders SET group_message_id=? WHERE id=?", (message_id, order_id))
            await db.commit()

    async def get_order(self, order_id: int):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
            return await cur.fetchone()

    async def get_worker_names(self, order_id: int) -> list[str]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """
                SELECT COALESCE(u.username, u.full_name) AS name
                FROM order_workers ow JOIN users u ON u.user_id = ow.worker_id
                WHERE ow.order_id=?
                """,
                (order_id,),
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    async def take_order(self, order_id: int, worker_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT workers_needed, workers_taken FROM orders WHERE id=?", (order_id,))
            order = await cur.fetchone()
            if not order or order["workers_taken"] >= order["workers_needed"]:
                return False

            try:
                await db.execute("INSERT INTO order_workers(order_id, worker_id) VALUES(?,?)", (order_id, worker_id))
            except aiosqlite.IntegrityError:
                return False

            new_taken = order["workers_taken"] + 1
            status = "closed" if new_taken >= order["workers_needed"] else "open"
            await db.execute(
                "UPDATE orders SET workers_taken=?, status=? WHERE id=?",
                (new_taken, status, order_id),
            )
            await db.commit()
            return True

    async def get_dispatcher_stats(self, user_id: int) -> tuple[int, int]:
        async with aiosqlite.connect(self.path) as db:
            cur1 = await db.execute("SELECT COUNT(*) FROM orders WHERE dispatcher_id=?", (user_id,))
            created = (await cur1.fetchone())[0]
            cur2 = await db.execute(
                """
                SELECT COUNT(*)
                FROM orders o
                JOIN order_workers ow ON o.id = ow.order_id
                WHERE ow.worker_id=?
                """,
                (user_id,),
            )
            completed = (await cur2.fetchone())[0]
            return created, completed

    async def set_premium(self, user_id: int, days: int = 30) -> None:
        until = (datetime.utcnow() + timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET premium_until=? WHERE user_id=?", (until, user_id))
            await db.execute(
                "INSERT INTO subscriptions(user_id, amount, period_days, status, created_at) VALUES(?,?,?,?,?)",
                (user_id, 99, days, "paid", datetime.utcnow().isoformat()),
            )
            await db.commit()
