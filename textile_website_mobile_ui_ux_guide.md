# Textile Website Mobile UI/UX Architecture Guide

This document outlines the detailed mobile UI/UX design specifications, component structures, and usability guidelines tailored for a Textile E-Commerce application. It covers the **Index (Home) Page**, **Shop (Product Listing) Page**, and **Admin Dashboard**.

---

## 1. Index Page (Home Page) UI/UX

The primary goal of the Home Page on mobile is to capture interest quickly, showcase fabric/category variety, and route users smoothly to the Shop page.

### 1.1 Header & Navigation
* **Dynamic Sticky Header:**
  * Top bar containing Brand Logo (Center), Hamburger Menu `≡` (Left), and Cart `🛒` / Wishlist `🤍` icons (Right).
  * **Behavior:** As the user scrolls down, the search bar auto-collapses into a subtle search icon to preserve screen real estate.
* **Interactive Search Bar:**
  * Displays a full-screen overlay when tapped.
  * Features **Popular Searches** (e.g., *Silk Sarees*, *Linen Shirts*, *Pure Cotton*) and **Recent Search History**.

### 1.2 Layout & Content Flow
1. **Stories-Style Category Bar:**
   * Horizontal circular avatars at the top (Instagram Story style): `New Arrivals`, `Sarees`, `Kurtis`, `Men's Cotton`, `Festive Sale`.
2. **Hero Carousel & Video Reels:**
   * High-definition promotional banners with smooth swipe gestures.
   * Auto-looping short video reels (5–8 seconds) demonstrating fabric shine, drape, and texture.
3. **Shop by Fabric Grid:**
   * Dedicated visual grid focusing on fabric types (*Pure Cotton, Kanchipuram Silk, Rayon, Linen, Chiffon*).
4. **Trending & Best Sellers (Horizontal Slider):**
   * Compact horizontal product cards with title, price, offer tag, and a direct `View Details` action.
5. **Trust & Guarantee Badges:**
   * A 3-column row with minimalist icons:
     * 🚚 **Free Shipping**
     * 💵 **Cash on Delivery**
     * 🔄 **Easy Returns & Quality Assured**

### 1.3 Persistent Navigation
* **Sticky Bottom Navigation Bar:**
  * Fixed at the bottom of the screen with 5 core tabs: `Home`, `Shop`, `Search`, `Wishlist`, and `Profile`.

---

## 2. Shop Page (Product Listing) UI/UX

The Shop Page focuses on quick browsing, filtering by fabric/size parameters, and seamless cart additions.

### 2.1 Layout & Display Modes
* **Grid Layout Switcher:**
  * A top toggle button allowing users to switch between **1-Column View** (large image, detailed view) and **2-Column Grid** (compact dual-card view).
* **Interactive Product Cards:**
  * **Color Swatches:** Embedded color dots under the thumbnail. Tapping a color dot updates the main image dynamically without reloading the page.
  * **Wishlist Action:** Quick-tap heart icon `🤍` on the top-right corner of each product image.
  * **Quick Add Drawer:** Tapping `Add +` opens a micro-drawer from the bottom to select size and add to cart immediately.

### 2.2 Filtering & Sorting
* **Sticky Bottom Action Bar:**
  * Dual sticky floating bar at the bottom: `[ ⇅ Sort By ]` | `[ ⚙ Filter ]`.
* **Bottom Slide-Up Filter Panel:**
  * Opens as a bottom sheet instead of a side drawer for easier thumb access.
  * **Filter Criteria:**
    * **Price Range:** Interactive min/max slider.
    * **Fabric Type:** Multi-select options (*Cotton, Silk, Linen, Synthetic*).
    * **Color Palette:** Visual color dots with selectable checkmarks.
    * **Pattern & Weave:** *Printed, Embroidery, Zari, Plain*.
    * **Size Selector:** *S, M, L, XL, XXL, Free Size*.
  * **Sticky Submit Button:** Shows live count (e.g., `Apply 4 Filters`).

---

## 3. Admin Page (Mobile Management Dashboard)

The Admin Page on mobile prioritizes speed, operational efficiency, and quick actions for managing daily textile sales.

### 3.1 Overview & Key Metrics
* **KPI Summary Cards (Swipeable Carousel):**
  * Displays real-time metrics: `Today's Revenue`, `Total Orders`, `Pending Shipments`, and `Low Stock Alerts`.
* **Floating Action Button (FAB):**
  * A persistent `+` button on the bottom right corner offering quick shortcuts:
    * ➕ **Add New Product**
    * 📦 **Create Manual Order / Invoice**
    * 🏷️ **Generate Coupon Code**

### 3.2 Order Management Workflow
* **Status Filter Tabs:**
  * Horizontal scrollable tabs: `All` | `Pending` | `Processing` | `Shipped` | `Delivered` | `Returns`.
* **Actionable Order Cards:**
  * Displays Order ID, Customer Name, Total Amount, and Payment Type (COD/Prepaid).
  * **Direct Actions:** One-tap **Call** or **WhatsApp** buttons to connect with the customer.
  * **Status Update:** Single-tap status changing dropdown (e.g., `Mark as Shipped`).

### 3.3 Product & Stock Management
* **Mobile Camera Integration:**
  * Direct photo capture via mobile camera with auto-cropping for multi-angle fabric uploads.
* **Rapid Stock Adjuster:**
  * Simple `+` and `-` counter inputs for fast inventory adjustments per variant (e.g., *Red - L size*).

---

## 4. Technical UI & Usability Principles

| Principle | Implementation Guidance |
| :--- | :--- |
| **Thumb Zone Alignment** | Place primary actions (Filter, Add to Cart, Order Status Update) within the lower 50% of the screen. |
| **Image Optimization** | Serve all images in WebP format with responsive size attributes (`srcset`) to ensure quick loads on mobile networks. |
| **Touch Target Size** | Ensure interactive targets are at least **44x44 pixels** with adequate spacing to prevent accidental taps. |