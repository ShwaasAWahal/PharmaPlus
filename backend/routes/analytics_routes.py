import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc

from database.db import db
from models.sales import Sale, SaleItem
from models.medicine import Medicine
from models.inventory import Inventory
from models.supplier import Supplier
from utils.jwt_utils import role_required

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _branch_filter(query, model, branch_id):
    if branch_id:
        return query.filter(model.branch_id == branch_id)
    return query


# ── GET /api/analytics/top-medicines ──────────────────────────────────────────

@analytics_bp.get("/top-medicines")
@jwt_required()
def top_medicines():
    """Top medicines by units sold in the given date range."""
    branch_id = request.args.get("branch_id", type=int)
    limit = min(request.args.get("limit", 10, type=int), 50)
    days = request.args.get("days", 30, type=int)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        db.session.query(
            Medicine.id,
            Medicine.name,
            Medicine.generic_name,
            Medicine.category,
            func.sum(SaleItem.quantity).label("total_units"),
            func.sum(SaleItem.line_total).label("total_revenue"),
            func.count(SaleItem.id).label("transaction_count"),
        )
        .join(SaleItem, SaleItem.medicine_id == Medicine.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.created_at >= since)
    )
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)

    rows = (
        query.group_by(Medicine.id, Medicine.name, Medicine.generic_name, Medicine.category)
        .order_by(desc("total_units"))
        .limit(limit)
        .all()
    )

    return jsonify({
        "success": True,
        "period_days": days,
        "top_medicines": [
            {
                "medicine_id": r.id,
                "name": r.name,
                "generic_name": r.generic_name,
                "category": r.category,
                "total_units_sold": int(r.total_units or 0),
                "total_revenue": round(float(r.total_revenue or 0), 2),
                "transaction_count": r.transaction_count,
            }
            for r in rows
        ],
    }), 200


# ── GET /api/analytics/monthly-revenue ────────────────────────────────────────

@analytics_bp.get("/monthly-revenue")
@jwt_required()
def monthly_revenue():
    """Monthly revenue aggregated for the last N months."""
    branch_id = request.args.get("branch_id", type=int)
    months = min(request.args.get("months", 12, type=int), 24)

    # Use SQLite/PG compatible strftime for year-month grouping
    # SQLAlchemy func.strftime works for SQLite; for Postgres use func.to_char
    try:
        month_label = func.strftime("%Y-%m", Sale.created_at)
        query = (
            db.session.query(
                month_label.label("month"),
                func.sum(Sale.total_amount).label("revenue"),
                func.count(Sale.id).label("transactions"),
            )
        )
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)

        since = datetime.now(timezone.utc) - timedelta(days=months * 31)
        query = query.filter(Sale.created_at >= since)
        rows = query.group_by("month").order_by("month").all()
    except Exception:
        rows = []

    return jsonify({
        "success": True,
        "months": months,
        "revenue_data": [
            {
                "month": r.month,
                "revenue": round(float(r.revenue or 0), 2),
                "transactions": r.transactions,
            }
            for r in rows
        ],
    }), 200


# ── GET /api/analytics/expired-stock ──────────────────────────────────────────

@analytics_bp.get("/expired-stock")
@jwt_required()
def expired_stock_report():
    """Summary of expired stock — count, quantity, estimated loss."""
    from services.inventory_service import get_expired_stock
    branch_id = request.args.get("branch_id", type=int)
    items = get_expired_stock(branch_id=branch_id)

    total_qty = sum(i.quantity for i in items)
    total_value_loss = sum(
        i.quantity * (i.purchase_price or i.medicine.purchase_price or 0)
        for i in items
    )

    return jsonify({
        "success": True,
        "total_expired_batches": len(items),
        "total_expired_units": total_qty,
        "estimated_value_loss": round(total_value_loss, 2),
        "items": [i.to_dict() for i in items],
    }), 200


# ── GET /api/analytics/supplier-performance ────────────────────────────────────

@analytics_bp.get("/supplier-performance")
@jwt_required()
@role_required("admin")
def supplier_performance():
    """Performance metrics per supplier."""
    rows = (
        db.session.query(
            Supplier.id,
            Supplier.name,
            Supplier.rating,
            func.count(Medicine.id).label("medicine_count"),
        )
        .outerjoin(Medicine, Medicine.supplier_id == Supplier.id)
        .filter(Supplier.is_active == True)
        .group_by(Supplier.id, Supplier.name, Supplier.rating)
        .order_by(desc(Supplier.rating))
        .all()
    )

    result = []
    for r in rows:
        # Count expired batches for this supplier's medicines
        expired = (
            db.session.query(func.count(Inventory.id))
            .join(Medicine, Medicine.id == Inventory.medicine_id)
            .filter(
                Medicine.supplier_id == r.id,
                Inventory.expiry_date < datetime.now(timezone.utc).date(),
                Inventory.quantity > 0,
            )
            .scalar()
        )
        result.append({
            "supplier_id": r.id,
            "supplier_name": r.name,
            "rating": r.rating,
            "total_medicines": r.medicine_count,
            "expired_batches": expired or 0,
        })

    return jsonify({"success": True, "suppliers": result}), 200


# ── GET /api/analytics/summary ─────────────────────────────────────────────────

@analytics_bp.get("/summary")
@jwt_required()
def dashboard_summary():
    """Quick KPIs for the admin dashboard."""
    from models.branch import Branch
    from models.user import User
    from datetime import date

    branch_id = request.args.get("branch_id", type=int)
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)

    sale_q = Sale.query
    if branch_id:
        sale_q = sale_q.filter_by(branch_id=branch_id)

    today_revenue = (
        sale_q.with_entities(func.sum(Sale.total_amount))
        .filter(func.date(Sale.created_at) == today)
        .scalar() or 0
    )
    month_revenue = (
        sale_q.with_entities(func.sum(Sale.total_amount))
        .filter(Sale.created_at >= month_start)
        .scalar() or 0
    )
    total_bills_today = (
        sale_q.filter(func.date(Sale.created_at) == today).count()
    )

    inv_q = Inventory.query.filter_by(is_active=True)
    if branch_id:
        inv_q = inv_q.filter_by(branch_id=branch_id)

    low_stock_count = inv_q.filter(
        Inventory.quantity <= Inventory.low_stock_threshold
    ).count()
    expiring_count = inv_q.filter(
        Inventory.expiry_date != None,
        Inventory.expiry_date <= (today + timedelta(days=30)),
        Inventory.expiry_date >= today,
        Inventory.quantity > 0,
    ).count()
    expired_count = inv_q.filter(
        Inventory.expiry_date != None,
        Inventory.expiry_date < today,
        Inventory.quantity > 0,
    ).count()

    return jsonify({
        "success": True,
        "today_revenue": round(float(today_revenue), 2),
        "month_revenue": round(float(month_revenue), 2),
        "total_bills_today": total_bills_today,
        "low_stock_count": low_stock_count,
        "expiring_soon_count": expiring_count,
        "expired_count": expired_count,
        "total_medicines": Medicine.query.filter_by(is_active=True).count(),
        "total_branches": Branch.query.filter_by(is_active=True).count(),
        "total_users": User.query.filter_by(is_active=True).count(),
    }), 200
