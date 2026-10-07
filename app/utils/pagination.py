"""
Pagination helper for Cosmos DB queries.
"""


class Pagination:
    """Pagination wrapper for query results."""

    def __init__(self, items: list, page: int, per_page: int, total: int):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = max(1, (total + per_page - 1) // per_page)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None

    @property
    def start_index(self) -> int:
        return (self.page - 1) * self.per_page + 1

    @property
    def end_index(self) -> int:
        return min(self.page * self.per_page, self.total)

    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        """Generate page numbers for pagination display with gaps."""
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                (self.page - left_current <= num <= self.page + right_current) or
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None  # gap marker
                yield num
                last = num

    def to_dict(self) -> dict:
        """Convert pagination info to dictionary for API responses."""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'total_pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_num': self.prev_num,
            'next_num': self.next_num
        }
