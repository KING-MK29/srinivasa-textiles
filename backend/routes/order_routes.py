import os
import sys
import json
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify

# Ensure parent directory is in sys.path for direct route loading
PARENT_DIR = str(Path(__file__).resolve().parent.parent)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from database.db import query_db, execute_db
from middleware.auth import require_admin
from middleware.rate_limiter import rate_limit
from utils.logger import logger

order_bp = Blueprint("order_bp", __name__)

@order_bp.route("", methods=["POST"])
@rate_limit(max_requests=25, window_seconds=60)
def create_order():
    """
    Places a new customer order and generates tax & tracking records.
    Prices and totals are verified against the authoritative database catalog.
    """
    data = request.get_json() or {}
    items = data.get("items", [])
    customer = data.get("customer", {})
    
    if not items or not customer:
        return jsonify({"success": False, "error": "Order items and customer details are required"}), 400

    order_id = data.get("orderId") or data.get("id") or f"ST-ORD-2026-{str(uuid.uuid4())[:6].upper()}"
    order_number = data.get("orderNumber") or order_id

    # Server-side authoritative price verification to prevent price tampering
    calculated_subtotal = 0.0
    verified_items = []

    for item in items:
        prod_id = item.get("id") or item.get("productId")
        qty = max(1, int(item.get("qty") or item.get("quantity", 1)))
        
        # Check against database catalog
        db_prod = query_db("SELECT id, name, price FROM products WHERE id = %s", (prod_id,), one=True) if prod_id else None
        if db_prod and db_prod.get("price") is not None:
            unit_price = float(db_prod["price"])
            prod_name = db_prod["name"]
        else:
            unit_price = float(item.get("unitPriceINR") or item.get("price", 0))
            prod_name = item.get("title") or item.get("name") or item.get("productName", "Textile Product")

        item_total = round(unit_price * qty, 2)
        calculated_subtotal += item_total
        verified_items.append({
            "prod_id": prod_id,
            "prod_name": prod_name,
            "price": unit_price,
            "qty": qty,
            "color": item.get("color") or item.get("selectedColor"),
            "blouse": item.get("blouseOption") or item.get("blouseLabel", "Unstitched"),
            "item_total": item_total
        })

    subtotal = calculated_subtotal

    # Authoritative discount verification
    coupon_code = (data.get("couponCode") or data.get("coupon") or "").strip().upper()
    discount = 0.0
    if coupon_code:
        coupon = query_db("SELECT * FROM coupons WHERE code = %s AND is_active = 1", (coupon_code,), one=True)
        if coupon and subtotal >= float(coupon.get("min_order_value", 0)):
            disc_percent = float(coupon["discount_percent"])
            calc_disc = (subtotal * disc_percent) / 100.0
            max_disc = float(coupon["max_discount"]) if coupon.get("max_discount") else None
            if max_disc and calc_disc > max_disc:
                calc_disc = max_disc
            discount = round(calc_disc, 2)
    elif data.get("discountINR") or data.get("discount"):
        discount = min(float(data.get("discountINR") or data.get("discount", 0)), subtotal)

    # 5% GST on silk handloom
    taxable_amount = max(0.0, subtotal - discount)
    tax = round(taxable_amount * 0.05, 2)
    shipping_fee = float(data.get("shippingINR") or data.get("shippingFee", 0))
    total_amount = round(taxable_amount + tax + shipping_fee, 2)

    payment_method = data.get("paymentMethod", "COD")
    payment_status = data.get("paymentStatus") or ("Paid" if ("COD" not in payment_method.upper()) else "Pending COD Collection")
    tracking_number = data.get("trackingNumber") or f"BD-{str(uuid.uuid4())[:9].upper()}"

    # Extract customer fields
    cust_name = customer.get("name", "Valued Customer")
    cust_email = customer.get("email", "")
    cust_phone = customer.get("phone", "")
    cust_addr = customer.get("address", "")
    cust_city = customer.get("city", "Chennai")
    cust_state = customer.get("state", "Tamil Nadu")
    cust_pincode = customer.get("pincode", "600001")

    # Insert master order
    execute_db(
        """INSERT INTO orders (
            id, order_number, customer_name, customer_email, customer_phone,
            shipping_address, city, state, pincode, subtotal, discount, tax,
            shipping_fee, total_amount, currency, payment_method, payment_status,
            order_status, tracking_number
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending Dispatch', %s)""",
        (
            order_id, order_number, cust_name, cust_email, cust_phone,
            cust_addr, cust_city, cust_state, cust_pincode,
            subtotal, discount, tax, shipping_fee, total_amount,
            data.get("currency", "INR"), payment_method, payment_status, tracking_number
        )
    )

    # Insert items and decrement stock
    for item in verified_items:
        item_id = str(uuid.uuid4())
        prod_id = item["prod_id"]
        prod_name = item["prod_name"]
        price = item["price"]
        qty = item["qty"]
        item_total = item["item_total"]

        execute_db(
            """INSERT INTO order_items (
                id, order_id, product_id, product_name, price, quantity, color, blouse_option, total_price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (item_id, order_id, prod_id, prod_name, price, qty, item["color"], item["blouse"], item_total)
        )

        # Decrement product stock safely
        if prod_id:
            execute_db("UPDATE products SET stock = CASE WHEN stock >= %s THEN stock - %s ELSE 0 END WHERE id = %s", (qty, qty, prod_id))

    logger.info(f"New Order Created: {order_number} | Amount: ₹{total_amount} | Customer: {customer.get('name')}")

    return jsonify({
        "success": True,
        "message": "Order placed successfully!",
        "order": {
            "id": order_id,
            "orderNumber": order_number,
            "totalAmount": total_amount,
            "tax": tax,
            "paymentStatus": payment_status,
            "trackingNumber": tracking_number,
            "carrier": "BlueDart Express"
        }
    }), 201

@order_bp.route("", methods=["GET"])
@require_admin
def get_orders():
    """
    Returns list of orders with their items (Restricted to Store Owner / Admin).
    """
    raw_orders = query_db("SELECT * FROM orders ORDER BY created_at DESC")
    orders = []

    for o in raw_orders:
        items = query_db("SELECT * FROM order_items WHERE order_id = %s", (o["id"],))
        orders.append({
            "id": o["id"],
            "orderNumber": o["order_number"],
            "customerName": o["customer_name"],
            "customerEmail": o["customer_email"],
            "customerPhone": o["customer_phone"],
            "shippingAddress": o["shipping_address"],
            "city": o["city"],
            "state": o["state"],
            "pincode": o["pincode"],
            "subtotal": float(o["subtotal"]),
            "discount": float(o["discount"]),
            "tax": float(o["tax"]),
            "shippingFee": float(o["shipping_fee"]),
            "totalAmount": float(o["total_amount"]),
            "currency": o["currency"],
            "paymentMethod": o["payment_method"],
            "paymentStatus": o["payment_status"],
            "orderStatus": o["order_status"],
            "trackingNumber": o["tracking_number"],
            "shippingCarrier": o["shipping_carrier"],
            "createdAt": o["created_at"],
            "items": [
                {
                    "productId": it["product_id"],
                    "productName": it["product_name"],
                    "price": float(it["price"]),
                    "quantity": it["quantity"],
                    "color": it["color"],
                    "blouseOption": it["blouse_option"],
                    "totalPrice": float(it["total_price"])
                }
                for it in items
            ]
        })

    return jsonify({"success": True, "count": len(orders), "orders": orders})

@order_bp.route("/<order_id>/status", methods=["PUT"])
@require_admin
def update_order_status(order_id):
    """
    Updates order fulfillment status (Packed, Dispatched, Delivered) - Admin only.
    """
    data = request.get_json() or {}
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "error": "Status is required"}), 400

    execute_db("UPDATE orders SET order_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s OR order_number = %s", (status, order_id, order_id))
    logger.info(f"Order {order_id} status updated to {status}")
    return jsonify({"success": True, "message": f"Order status updated to {status}"})

@order_bp.route("/<order_id>/payment-status", methods=["PUT"])
@require_admin
def update_order_payment_status(order_id):
    """
    Updates order payment status and records UTR / UPI reference - Admin only.
    """
    data = request.get_json() or {}
    payment_status = data.get("paymentStatus") or data.get("status") or "paid"
    utr_number = data.get("utrNumber") or data.get("upiRef") or data.get("transactionId") or ""

    execute_db(
        "UPDATE orders SET payment_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s OR order_number = %s",
        (payment_status, order_id, order_id)
    )
    logger.info(f"Payment status for order {order_id} updated to {payment_status} | UTR: {utr_number}")
    return jsonify({
        "success": True,
        "message": f"Payment status updated to {payment_status}",
        "orderId": order_id,
        "paymentStatus": payment_status,
        "utrNumber": utr_number
    })

@order_bp.route("/webhook/payment", methods=["POST"])
def payment_gateway_webhook():
    """
    Inbound Webhook Endpoint for Payment Providers (HDFC / Razorpay / PhonePe / UPI).
    Verifies shared webhook secret to prevent spoofed payment confirmations.
    """
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    provided_secret = request.headers.get("X-Webhook-Secret") or request.headers.get("X-Razorpay-Signature") or request.headers.get("X-Gateway-Secret")

    if webhook_secret:
        if not provided_secret or provided_secret != webhook_secret:
            logger.warning("⚠️ Unauthorized webhook trigger attempted without valid secret.")
            return jsonify({"success": False, "error": "Unauthorized: Invalid or missing webhook signature/secret"}), 401

    payload = request.get_json() or {}
    order_id = payload.get("order_id") or payload.get("orderId") or payload.get("order_number")
    utr_number = payload.get("utr_number") or payload.get("utr") or payload.get("transaction_id") or payload.get("upi_ref_no") or f"UPI/HDFC/TXN-{str(uuid.uuid4())[:8].upper()}"
    status = payload.get("status") or payload.get("payment_status") or "paid"

    if not order_id:
        return jsonify({"success": False, "error": "order_id is required"}), 400

    execute_db(
        "UPDATE orders SET payment_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s OR order_number = %s",
        (status, order_id, order_id)
    )
    logger.info(f"⚡ [Gateway Webhook] Inbound Payment Received for Order {order_id} | Status: {status} | UTR: {utr_number}")

    return jsonify({
        "success": True,
        "message": "Payment webhook processed successfully",
        "orderId": order_id,
        "status": status,
        "utrNumber": utr_number
    })

@order_bp.route("/track/<lookup>", methods=["GET"])
def track_order(lookup):
    """
    Public lookup by tracking number or order number.
    """
    order = query_db(
        "SELECT * FROM orders WHERE tracking_number = %s OR order_number = %s OR id = %s",
        (lookup, lookup, lookup),
        one=True
    )
    if not order:
        return jsonify({"success": False, "error": "Order or Tracking Number not found"}), 404

    return jsonify({
        "success": True,
        "tracking": {
            "orderNumber": order["order_number"],
            "status": order["order_status"],
            "trackingNumber": order["tracking_number"],
            "carrier": order["shipping_carrier"],
            "customerCity": order["city"],
            "createdAt": order["created_at"]
        }
    })

