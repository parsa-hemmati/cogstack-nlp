"""Search analytics service for query tracking and analysis.

Provides:
- Top queries analysis
- Zero-result query identification
- Search volume metrics
- Click-through rate analysis
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from uuid import UUID
import logging

from app.models.search_analytic import SearchAnalytic
from app.models.user import User

logger = logging.getLogger(__name__)


class SearchAnalyticsService:
    """Service for search analytics tracking and reporting."""

    def __init__(self, db: AsyncSession):
        """
        Initialize search analytics service.

        Args:
            db: Async database session
        """
        self.db = db

    async def track_search(
        self,
        user_id: UUID,
        query: str,
        filters: Optional[Dict[str, Any]],
        total_results: int,
        page: int,
        execution_time_ms: int,
        session_id: Optional[UUID] = None
    ) -> SearchAnalytic:
        """
        Track a search query.

        Args:
            user_id: User executing search
            query: Search query string
            filters: Applied filters (document_type, date_from, etc.)
            total_results: Number of results found
            page: Page number
            execution_time_ms: Query execution time
            session_id: Optional session ID for grouping

        Returns:
            Created SearchAnalytic record
        """
        try:
            analytic = SearchAnalytic(
                user_id=user_id,
                query=query,
                filters=filters,
                total_results=total_results,
                page=page,
                execution_time_ms=execution_time_ms,
                session_id=session_id
            )

            self.db.add(analytic)
            await self.db.commit()
            await self.db.refresh(analytic)

            logger.info(f"Tracked search: query='{query}', results={total_results}")
            return analytic

        except Exception as e:
            logger.error(f"Failed to track search: {e}")
            await self.db.rollback()
            raise

    async def track_click(
        self,
        search_id: UUID,
        clicked_result_id: UUID,
        clicked_result_rank: int
    ) -> bool:
        """
        Track a click on search result.

        Args:
            search_id: Search analytic record ID
            clicked_result_id: Document ID that was clicked
            clicked_result_rank: Position in results (1, 2, 3, ...)

        Returns:
            True if updated successfully
        """
        try:
            result = await self.db.execute(
                select(SearchAnalytic).where(SearchAnalytic.id == search_id)
            )
            analytic = result.scalar_one_or_none()

            if not analytic:
                logger.warning(f"Search analytic {search_id} not found")
                return False

            analytic.clicked_result_id = clicked_result_id
            analytic.clicked_result_rank = clicked_result_rank

            await self.db.commit()

            logger.info(f"Tracked click: search={search_id}, rank={clicked_result_rank}")
            return True

        except Exception as e:
            logger.error(f"Failed to track click: {e}")
            await self.db.rollback()
            raise

    async def get_top_queries(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get top search queries by frequency.

        Args:
            date_from: Start date
            date_to: End date
            limit: Maximum results

        Returns:
            List of {query, count} dictionaries
        """
        try:
            query = (
                select(
                    SearchAnalytic.query,
                    func.count(SearchAnalytic.id).label('count')
                )
                .where(
                    and_(
                        SearchAnalytic.created_at >= date_from,
                        SearchAnalytic.created_at <= date_to
                    )
                )
                .group_by(SearchAnalytic.query)
                .order_by(func.count(SearchAnalytic.id).desc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            rows = result.all()

            return [
                {"query": row.query, "count": row.count}
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get top queries: {e}")
            raise

    async def get_zero_result_queries(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get queries that returned zero results.

        Args:
            date_from: Start date
            date_to: End date
            limit: Maximum results

        Returns:
            List of {query, count} dictionaries
        """
        try:
            query = (
                select(
                    SearchAnalytic.query,
                    func.count(SearchAnalytic.id).label('count')
                )
                .where(
                    and_(
                        SearchAnalytic.created_at >= date_from,
                        SearchAnalytic.created_at <= date_to,
                        SearchAnalytic.total_results == 0
                    )
                )
                .group_by(SearchAnalytic.query)
                .order_by(func.count(SearchAnalytic.id).desc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            rows = result.all()

            return [
                {"query": row.query, "count": row.count}
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get zero-result queries: {e}")
            raise

    async def get_analytics_summary(
        self,
        date_from: datetime,
        date_to: datetime
    ) -> Dict[str, Any]:
        """
        Get analytics summary for date range.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            Dictionary with analytics metrics
        """
        try:
            # Total searches
            total_query = select(func.count(SearchAnalytic.id)).where(
                and_(
                    SearchAnalytic.created_at >= date_from,
                    SearchAnalytic.created_at <= date_to
                )
            )
            total_result = await self.db.execute(total_query)
            total_searches = total_result.scalar()

            # Unique users
            unique_users_query = select(func.count(func.distinct(SearchAnalytic.user_id))).where(
                and_(
                    SearchAnalytic.created_at >= date_from,
                    SearchAnalytic.created_at <= date_to
                )
            )
            unique_result = await self.db.execute(unique_users_query)
            unique_users = unique_result.scalar()

            # Average results per query
            avg_results_query = select(func.avg(SearchAnalytic.total_results)).where(
                and_(
                    SearchAnalytic.created_at >= date_from,
                    SearchAnalytic.created_at <= date_to
                )
            )
            avg_result = await self.db.execute(avg_results_query)
            avg_results = avg_result.scalar() or 0.0

            # Average response time
            avg_time_query = select(func.avg(SearchAnalytic.execution_time_ms)).where(
                and_(
                    SearchAnalytic.created_at >= date_from,
                    SearchAnalytic.created_at <= date_to,
                    SearchAnalytic.execution_time_ms.isnot(None)
                )
            )
            avg_time_result = await self.db.execute(avg_time_query)
            avg_response_time = avg_time_result.scalar() or 0.0

            # Click-through rate (searches with clicks / total searches)
            clicks_query = select(func.count(SearchAnalytic.id)).where(
                and_(
                    SearchAnalytic.created_at >= date_from,
                    SearchAnalytic.created_at <= date_to,
                    SearchAnalytic.clicked_result_id.isnot(None)
                )
            )
            clicks_result = await self.db.execute(clicks_query)
            searches_with_clicks = clicks_result.scalar()

            click_through_rate = (searches_with_clicks / total_searches * 100) if total_searches > 0 else 0.0

            return {
                "total_searches": total_searches,
                "unique_users": unique_users,
                "avg_results_per_query": round(avg_results, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "click_through_rate": round(click_through_rate, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            raise

    async def get_full_analytics(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get complete analytics report.

        Args:
            date_from: Start date
            date_to: End date
            limit: Maximum results for top/zero-result queries

        Returns:
            Complete analytics dictionary
        """
        try:
            summary = await self.get_analytics_summary(date_from, date_to)
            top_queries = await self.get_top_queries(date_from, date_to, limit)
            zero_result_queries = await self.get_zero_result_queries(date_from, date_to, limit)

            return {
                "date_range": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat()
                },
                **summary,
                "top_queries": top_queries,
                "zero_result_queries": zero_result_queries
            }

        except Exception as e:
            logger.error(f"Failed to get full analytics: {e}")
            raise
