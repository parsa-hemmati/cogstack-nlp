"""
AnalyticsService for search analytics aggregation and reporting.

Provides methods to analyze search patterns, identify issues, and track trends.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.search_analytics import SearchAnalytics


class AnalyticsService:
    """Service for aggregating and analyzing search analytics data."""

    async def get_top_queries(
        self,
        db: AsyncSession,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most frequently searched queries.

        Args:
            db: Database session
            limit: Maximum number of queries to return
            start_date: Filter queries after this date
            end_date: Filter queries before this date
            user_id: Filter by specific user

        Returns:
            List of dicts with 'query' and 'count' keys, sorted by count descending
        """
        # Build query
        query = select(
            SearchAnalytics.query,
            func.count(SearchAnalytics.id).label('count')
        )

        # Apply filters
        filters = []
        if start_date:
            filters.append(SearchAnalytics.created_at >= start_date)
        if end_date:
            filters.append(SearchAnalytics.created_at <= end_date)
        if user_id:
            filters.append(SearchAnalytics.user_id == user_id)

        if filters:
            query = query.where(and_(*filters))

        # Group by query and order by count
        query = (
            query.group_by(SearchAnalytics.query)
            .order_by(func.count(SearchAnalytics.id).desc())
            .limit(limit)
        )

        # Execute
        result = await db.execute(query)
        rows = result.all()

        return [
            {"query": row.query, "count": row.count}
            for row in rows
        ]

    async def get_zero_result_queries(
        self,
        db: AsyncSession,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get queries that returned zero results.

        Useful for identifying missing content or poor query formulation.

        Args:
            db: Database session
            limit: Maximum number of queries to return
            start_date: Filter queries after this date
            end_date: Filter queries before this date

        Returns:
            List of dicts with 'query' and 'count' keys
        """
        # Build query
        query = select(
            SearchAnalytics.query,
            func.count(SearchAnalytics.id).label('count')
        ).where(SearchAnalytics.results_count == 0)

        # Apply filters
        filters = []
        if start_date:
            filters.append(SearchAnalytics.created_at >= start_date)
        if end_date:
            filters.append(SearchAnalytics.created_at <= end_date)

        if filters:
            query = query.where(and_(*filters))

        # Group by query and order by count
        query = (
            query.group_by(SearchAnalytics.query)
            .order_by(func.count(SearchAnalytics.id).desc())
            .limit(limit)
        )

        # Execute
        result = await db.execute(query)
        rows = result.all()

        return [
            {"query": row.query, "count": row.count}
            for row in rows
        ]

    async def get_slow_queries(
        self,
        db: AsyncSession,
        limit: int = 10,
        threshold_ms: int = 2000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get slowest queries above execution time threshold.

        Useful for identifying performance issues.

        Args:
            db: Database session
            limit: Maximum number of queries to return
            threshold_ms: Minimum execution time in milliseconds
            start_date: Filter queries after this date
            end_date: Filter queries before this date

        Returns:
            List of dicts with 'query', 'execution_time_ms', 'count' keys
        """
        # Build query
        query = select(
            SearchAnalytics.query,
            func.avg(SearchAnalytics.execution_time_ms).label('avg_execution_time_ms'),
            func.max(SearchAnalytics.execution_time_ms).label('execution_time_ms'),
            func.count(SearchAnalytics.id).label('count')
        ).where(SearchAnalytics.execution_time_ms >= threshold_ms)

        # Apply filters
        filters = []
        if start_date:
            filters.append(SearchAnalytics.created_at >= start_date)
        if end_date:
            filters.append(SearchAnalytics.created_at <= end_date)

        if filters:
            query = query.where(and_(*filters))

        # Group by query and order by max execution time
        query = (
            query.group_by(SearchAnalytics.query)
            .order_by(func.max(SearchAnalytics.execution_time_ms).desc())
            .limit(limit)
        )

        # Execute
        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "query": row.query,
                "execution_time_ms": int(row.execution_time_ms),
                "avg_execution_time_ms": int(row.avg_execution_time_ms),
                "count": row.count
            }
            for row in rows
        ]

    async def get_search_trends(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get search volume trends by date.

        Useful for understanding usage patterns over time.

        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of dicts with 'date' and 'count' keys, ordered by date
        """
        # Build query - use date function to extract date from datetime
        # Use SQLite-compatible date function
        query = select(
            func.date(SearchAnalytics.created_at).label('date'),
            func.count(SearchAnalytics.id).label('count')
        ).where(
            and_(
                SearchAnalytics.created_at >= start_date,
                SearchAnalytics.created_at <= end_date
            )
        )

        # Group by date and order chronologically
        query = (
            query.group_by(func.date(SearchAnalytics.created_at))
            .order_by(func.date(SearchAnalytics.created_at))
        )

        # Execute
        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "date": str(row.date),  # SQLite returns date as string
                "count": row.count
            }
            for row in rows
        ]
