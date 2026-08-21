"""
Nexus360 — Market Intelligence & Portfolio Context Router.

Provides real-time and institutional market quotes, historical time-series charts,
and client portfolio opportunity analytics for Relationship Managers and Wealth Advisors.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.market_service import market_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/market", tags=["Market Intelligence"])


@router.get("/quotes", summary="Get Tracked Market Quotes")
async def get_market_quotes(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Retrieve live/latest market quotes for top tracked equities and instruments.
    """
    return await market_service.get_market_quotes()


@router.get("/timeseries", summary="Get Instrument Time-Series History")
async def get_instrument_timeseries(
    symbol: str = Query("TCS", description="Instrument ticker symbol (e.g. TCS, INFY, RELIANCE, IBM)"),
    time_range: str = Query("1M", alias="range", description="Time range (1D, 1W, 1M, 3M, 6M)"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Retrieve time-series price data points and metrics for chart visualization.
    """
    return await market_service.get_time_series(symbol=symbol, time_range=time_range)


@router.get("/portfolio-context", summary="Get Client Portfolio Opportunities Context")
async def get_portfolio_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Retrieve aggregated client portfolio metrics and cross-asset opportunities for Relationship Managers.
    """
    return await market_service.get_portfolio_context(session=db)
