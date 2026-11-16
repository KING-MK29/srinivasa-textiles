import os
import sys
import time
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify

# Ensure parent directory is in sys.path
PARENT_DIR = str(Path(__file__).resolve().parent.parent)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from database.db import query_db, execute_db, get_db_type
from middleware.auth import require_admin
from middleware.rate_limiter import rate_limit

utility_bp = Blueprint("utility_bp", __name__)
START_TIME = time.time()

@utility_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check and diagnostics endpoint for monitoring and uptime trackers.
    """
    db_status = "healthy"
    try:
        query_db("SELECT 1", one=True)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    uptime_seconds = int(time.time() - START_TIME)

    return jsonify({
        "status": "online" if db_status == "healthy" else "degraded",
        "service": "Srinivasa Textiles REST Engine",
        "version": "2.4.0",
        "databaseEngine": get_db_type(),
        "databaseStatus": db_status,
        "uptimeSeconds": uptime_seconds,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

@utility_bp.route("/coupons/validate", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60)
def validate_coupon():
    """
    Validates a promo code against the cart subtotal.
    """
    data = request.get_json() or {}
    code = data.get("code", "").strip().upper()
    subtotal = float(data.get("subtotal", 0))

    if not code:
        return jsonify({"success": False, "error": "Coupon code is required"}), 400

    coupon = query_db("SELECT * FROM coupons WHERE code = %s AND is_active = 1", (code,), one=True)
    if not coupon:
        return jsonify({"success": False, "error": "Invalid or expired promotional coupon code"}), 404

    min_val = float(coupon.get("min_order_value", 0))
    if subtotal < min_val:
        return jsonify({
            "success": False,
            "error": f"Coupon {code} requires a minimum cart value of ₹{min_val:,.0f}"
        }), 400

    discount_percent = float(coupon["discount_percent"])
    discount_amount = (subtotal * discount_percent) / 100.0
    max_discount = float(coupon["max_discount"]) if coupon.get("max_discount") else None

    if max_discount and discount_amount > max_discount:
        discount_amount = max_discount

    return jsonify({
        "success": True,
        "coupon": {
            "code": code,
            "discountPercent": discount_percent,
            "discountAmount": round(discount_amount, 2),
            "maxDiscount": max_discount
        }
    })

@utility_bp.route("/coupons", methods=["GET"])
def get_coupons():
    """
    Returns all coupons from the database.
    """
    coupons = query_db("SELECT * FROM coupons ORDER BY created_at DESC")
    return jsonify({"success": True, "count": len(coupons), "coupons": coupons})

@utility_bp.route("/coupons", methods=["POST"])
@require_admin
def create_coupon():
    """
    Creates a new coupon (Admin only).
    """
    data = request.get_json() or {}
    code = data.get("code", "").strip().upper()
    discount_percent = float(data.get("discount_percent", 10.0))
    max_discount = float(data.get("max_discount")) if data.get("max_discount") else None
    min_order_value = float(data.get("min_order_value", 0.0))
    is_active = 1 if data.get("is_active", True) else 0
    valid_until = data.get("valid_until")

    if not code:
        return jsonify({"success": False, "error": "Coupon code is required"}), 400

    existing = query_db("SELECT id FROM coupons WHERE code = %s", (code,), one=True)
    if existing:
        return jsonify({"success": False, "error": f"Coupon {code} already exists"}), 409

    coupon_id = f"cp-{uuid.uuid4().hex[:8]}"
    execute_db(
        "INSERT INTO coupons (id, code, discount_percent, max_discount, min_order_value, is_active, valid_until) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (coupon_id, code, discount_percent, max_discount, min_order_value, is_active, valid_until)
    )

    return jsonify({"success": True, "message": f"Coupon {code} created successfully", "couponId": coupon_id}), 201

@utility_bp.route("/coupons/<coupon_id>", methods=["PUT"])
@require_admin
def update_coupon(coupon_id):
    """
    Updates / Alters an existing coupon (Admin only).
    """
    data = request.get_json() or {}
    existing = query_db("SELECT * FROM coupons WHERE id = %s", (coupon_id,), one=True)
    if not existing:
        return jsonify({"success": False, "error": "Coupon not found"}), 404

    code = data.get("code", existing["code"]).strip().upper()
    discount_percent = float(data.get("discount_percent", existing["discount_percent"]))
    max_discount = float(data.get("max_discount")) if data.get("max_discount") is not None else existing["max_discount"]
    min_order_value = float(data.get("min_order_value", existing["min_order_value"]))
    is_active = 1 if data.get("is_active", bool(existing["is_active"])) else 0
    valid_until = data.get("valid_until", existing.get("valid_until"))

    execute_db(
        "UPDATE coupons SET code = %s, discount_percent = %s, max_discount = %s, min_order_value = %s, is_active = %s, valid_until = %s WHERE id = %s",
        (code, discount_percent, max_discount, min_order_value, is_active, valid_until, coupon_id)
    )

    return jsonify({"success": True, "message": f"Coupon {code} updated successfully"})

@utility_bp.route("/coupons/<coupon_id>", methods=["DELETE"])
@require_admin
def delete_coupon(coupon_id):
    """
    Removes / deletes a coupon (Admin only).
    """
    existing = query_db("SELECT * FROM coupons WHERE id = %s", (coupon_id,), one=True)
    if not existing:
        return jsonify({"success": False, "error": "Coupon not found"}), 404

    execute_db("DELETE FROM coupons WHERE id = %s", (coupon_id,))
    return jsonify({"success": True, "message": f"Coupon {existing['code']} deleted successfully"})

@utility_bp.route("/reviews", methods=["GET"])
def get_reviews():
    """
    Returns verified reviews.
    """
    product_id = request.args.get("productId")
    if product_id:
        reviews = query_db("SELECT * FROM reviews WHERE product_id = %s ORDER BY created_at DESC", (product_id,))
    else:
        reviews = query_db("SELECT * FROM reviews ORDER BY created_at DESC LIMIT 50")

    return jsonify({"success": True, "count": len(reviews), "reviews": reviews})

@utility_bp.route("/subscribers", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def add_subscriber():
    """
    Adds a new newsletter / restock subscriber with input validation.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()

    if not email or "@" not in email or "." not in email:
        return jsonify({"success": False, "error": "A valid email address is required"}), 400

    existing = query_db("SELECT id FROM subscribers WHERE email = %s", (email,), one=True)
    if not existing:
        sub_id = str(uuid.uuid4())
        execute_db("INSERT INTO subscribers (id, email, phone) VALUES (%s, %s, %s)", (sub_id, email, phone))

    return jsonify({"success": True, "message": "Successfully subscribed to Srinivasa Heritage Circle!"})

# ==========================================
# PRODUCT & MEDIA UPLOAD ENDPOINT
# ==========================================
import base64
import re
from werkzeug.utils import secure_filename

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "svg", "bmp", "avif"}

@utility_bp.route("/upload", methods=["POST"])
def upload_product_image():
    """
    Accepts multipart/form-data with 'file' or JSON with 'image' (base64 DataURL).
    Saves image into frontend/uploads/ directory.
    Returns JSON: { "success": True, "url": "uploads/prod_173158...jpg", "filename": "prod_..." }
    """
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Handle multipart form-data
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                orig_name = secure_filename(file.filename) or "image.jpg"
                ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else "jpg"
                if ext not in ALLOWED_EXTENSIONS:
                    ext = "jpg"
                safe_name = f"prod_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.{ext}"
                target_path = UPLOAD_DIR / safe_name
                file.save(str(target_path))
                return jsonify({
                    "success": True,
                    "url": f"uploads/{safe_name}",
                    "filename": safe_name
                })

        # 2. Handle JSON base64 data
        json_data = request.get_json(silent=True) or {}
        image_data = json_data.get("image") or json_data.get("dataUrl")
        if image_data and isinstance(image_data, str):
            match = re.match(r"^data:image/([a-zA-Z0-9\+\-]+);base64,(.+)$", image_data, re.DOTALL)
            if match:
                raw_ext = match.group(1).lower()
                ext = "jpg" if raw_ext in ["jpeg", "jpg"] else ("png" if raw_ext == "png" else ("webp" if raw_ext == "webp" else "jpg"))
                b64_str = match.group(2)
            else:
                ext = "jpg"
                b64_str = image_data

            binary_data = base64.b64decode(b64_str)
            safe_name = f"prod_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.{ext}"
            target_path = UPLOAD_DIR / safe_name
            with open(target_path, "wb") as f:
                f.write(binary_data)

            return jsonify({
                "success": True,
                "url": f"uploads/{safe_name}",
                "filename": safe_name
            })

        return jsonify({"success": False, "error": "No file or image data provided"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
