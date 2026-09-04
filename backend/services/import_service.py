import csv
import io
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional, Set
import logging
from backend.database.connection import get_db_connection
from backend.models.import_data import (
    ValidationErrorItem,
    DatasetPreview,
    CombinedPreviewResponse,
    ImportSummaryResponse,
    ImportStatusResponse,
)
from backend.database.seed import seed_database
from backend.services.version_service import DataVersionService

logger = logging.getLogger("retail_copilot.import")

REQUIRED_COLUMNS = {
    "products": {"sku", "product_name", "category", "unit_price", "reorder_level"},
    "stores": {"store_code", "store_name", "city"},
    "sales": {"sale_date", "store_code", "sku", "quantity", "unit_price", "revenue"},
    "inventory": {"store_code", "sku", "stock_quantity"},
}


HEADER_ALIASES = {
    "date": "sale_date",
    "transaction_date": "sale_date",
    "units_sold": "quantity",
    "units": "quantity",
    "qty": "quantity",
    "stock_level": "stock_quantity",
    "stock": "stock_quantity",
    "current_stock": "stock_quantity",
    "region": "city",
    "location": "city",
    "price": "unit_price",
    "name": "product_name",
    "item_name": "product_name",
}


class ImportService:
    @staticmethod
    def get_status() -> ImportStatusResponse:
        """Query current total counts from SQLite database."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stores")
            stores_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM products")
            products_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM sales")
            sales_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM inventory")
            inventory_count = cursor.fetchone()[0]

        return ImportStatusResponse(
            stores_count=stores_count,
            products_count=products_count,
            sales_count=sales_count,
            inventory_count=inventory_count,
        )

    @staticmethod
    def parse_csv_content(file_bytes: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
        """Decode CSV bytes and parse into list of row dicts with normalized headers."""
        try:
            # Handle UTF-8 with or without BOM, or fallback to latin-1
            try:
                decoded = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                decoded = file_bytes.decode("latin-1")

            reader = csv.reader(io.StringIO(decoded))
            rows_raw = list(reader)
            if not rows_raw:
                return [], []

            # Normalize headers (lowercase, trimmed, and apply aliases)
            raw_headers = rows_raw[0]
            canonical_headers: List[str] = []
            for h in raw_headers:
                if h is not None:
                    h_clean = h.strip().lower()
                    canonical = HEADER_ALIASES.get(h_clean, h_clean)
                    canonical_headers.append(canonical)

            rows: List[Dict[str, str]] = []
            for line_idx, raw_row in enumerate(rows_raw[1:], start=2):
                if not any(col.strip() for col in raw_row if col):
                    continue  # Skip empty lines

                row_dict: Dict[str, str] = {}
                for h_idx, header in enumerate(canonical_headers):
                    val = raw_row[h_idx].strip() if h_idx < len(raw_row) else ""
                    row_dict[header] = val
                row_dict["_row_number"] = line_idx
                rows.append(row_dict)

            return canonical_headers, rows
        except Exception as e:
            logger.error(f"Error parsing CSV content: {e}")
            raise ValueError(f"Unable to parse CSV file: {str(e)}")

    @classmethod
    def validate_products_rows(
        cls,
        rows: List[Dict[str, Any]],
        existing_skus: Optional[Set[str]] = None,
        check_db_duplicates: bool = False,
    ) -> List[ValidationErrorItem]:
        """Validate product catalog records."""
        errors: List[ValidationErrorItem] = []
        seen_skus: Set[str] = set()

        for row in rows:
            row_num = row.get("_row_number", 0)
            sku = str(row.get("sku", "")).strip()
            name = str(row.get("product_name", "")).strip()
            cat = str(row.get("category", "")).strip()
            price_raw = str(row.get("unit_price", "")).strip()
            reorder_raw = str(row.get("reorder_level", "")).strip()

            if not sku:
                errors.append(ValidationErrorItem(row_number=row_num, field="sku", message="SKU cannot be empty", raw_data=row))
            elif sku in seen_skus:
                errors.append(ValidationErrorItem(row_number=row_num, field="sku", message=f"Duplicate SKU '{sku}' found in uploaded file", raw_data=row))
            else:
                seen_skus.add(sku)
                if check_db_duplicates and existing_skus and sku in existing_skus:
                    errors.append(ValidationErrorItem(row_number=row_num, field="sku", message=f"SKU '{sku}' already exists in database", raw_data=row))

            if not name:
                errors.append(ValidationErrorItem(row_number=row_num, field="product_name", message="Product name cannot be empty", raw_data=row))

            if not cat:
                errors.append(ValidationErrorItem(row_number=row_num, field="category", message="Category cannot be empty", raw_data=row))

            try:
                price = float(price_raw)
                if price < 0:
                    errors.append(ValidationErrorItem(row_number=row_num, field="unit_price", message="Unit price must be >= 0", raw_data=row))
            except (ValueError, TypeError):
                errors.append(ValidationErrorItem(row_number=row_num, field="unit_price", message=f"Unit price '{price_raw}' must be a valid number", raw_data=row))

            try:
                reorder = float(reorder_raw)
                if reorder < 0:
                    errors.append(ValidationErrorItem(row_number=row_num, field="reorder_level", message="Reorder level must be >= 0", raw_data=row))
            except (ValueError, TypeError):
                errors.append(ValidationErrorItem(row_number=row_num, field="reorder_level", message=f"Reorder level '{reorder_raw}' must be a valid number", raw_data=row))

        return errors

    @classmethod
    def validate_stores_rows(
        cls,
        rows: List[Dict[str, Any]],
        existing_codes: Optional[Set[str]] = None,
        check_db_duplicates: bool = False,
    ) -> List[ValidationErrorItem]:
        """Validate store records."""
        errors: List[ValidationErrorItem] = []
        seen_codes: Set[str] = set()

        for row in rows:
            row_num = row.get("_row_number", 0)
            code = str(row.get("store_code", "")).strip()
            name = str(row.get("store_name", "")).strip()
            city = str(row.get("city", "")).strip()

            if not code:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message="Store code cannot be empty", raw_data=row))
            elif code in seen_codes:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message=f"Duplicate store_code '{code}' found in uploaded file", raw_data=row))
            else:
                seen_codes.add(code)
                if check_db_duplicates and existing_codes and code in existing_codes:
                    errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message=f"Store code '{code}' already exists in database", raw_data=row))

            if not name:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_name", message="Store name cannot be empty", raw_data=row))

            if not city:
                errors.append(ValidationErrorItem(row_number=row_num, field="city", message="City cannot be empty", raw_data=row))

        return errors

    @classmethod
    def validate_sales_rows(
        cls,
        rows: List[Dict[str, Any]],
        known_stores: Set[str],
        known_skus: Set[str],
    ) -> List[ValidationErrorItem]:
        """Validate sales transaction records and foreign key references."""
        errors: List[ValidationErrorItem] = []

        for row in rows:
            row_num = row.get("_row_number", 0)
            date_raw = str(row.get("sale_date", "")).strip()
            store_code = str(row.get("store_code", "")).strip()
            sku = str(row.get("sku", "")).strip()
            qty_raw = str(row.get("quantity", "")).strip()
            price_raw = str(row.get("unit_price", "")).strip()
            rev_raw = str(row.get("revenue", "")).strip()

            # Date check
            if not date_raw:
                errors.append(ValidationErrorItem(row_number=row_num, field="sale_date", message="Sale date cannot be empty", raw_data=row))
            else:
                try:
                    # Support standard ISO date format YYYY-MM-DD or timestamp
                    date_part = date_raw.split("T")[0].split(" ")[0]
                    datetime.strptime(date_part, "%Y-%m-%d")
                except ValueError:
                    errors.append(ValidationErrorItem(row_number=row_num, field="sale_date", message=f"Invalid date format '{date_raw}', expected YYYY-MM-DD", raw_data=row))

            # Store foreign key
            if not store_code:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message="store_code cannot be empty", raw_data=row))
            elif store_code not in known_stores:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message=f"store_code '{store_code}' does not exist", raw_data=row))

            # SKU foreign key
            if not sku:
                errors.append(ValidationErrorItem(row_number=row_num, field="sku", message="SKU cannot be empty", raw_data=row))
            elif sku not in known_skus:
                errors.append(ValidationErrorItem(row_number=row_num, field="sku", message=f"SKU '{sku}' does not exist", raw_data=row))

            # Quantity check
            try:
                qty = int(qty_raw)
                if qty <= 0:
                    errors.append(ValidationErrorItem(row_number=row_num, field="quantity", message="Quantity must be greater than 0", raw_data=row))
            except (ValueError, TypeError):
                errors.append(ValidationErrorItem(row_number=row_num, field="quantity", message=f"Quantity '{qty_raw}' must be a valid positive integer", raw_data=row))

            # Price & Revenue check
            price_val = None
            rev_val = None

            if price_raw:
                try:
                    price_val = float(price_raw)
                    if price_val < 0:
                        errors.append(ValidationErrorItem(row_number=row_num, field="unit_price", message="Unit price must be >= 0", raw_data=row))
                except (ValueError, TypeError):
                    errors.append(ValidationErrorItem(row_number=row_num, field="unit_price", message=f"Unit price '{price_raw}' must be a valid number", raw_data=row))

            if rev_raw:
                try:
                    rev_val = float(rev_raw)
                    if rev_val < 0:
                        errors.append(ValidationErrorItem(row_number=row_num, field="revenue", message="Revenue must be >= 0", raw_data=row))
                except (ValueError, TypeError):
                    errors.append(ValidationErrorItem(row_number=row_num, field="revenue", message=f"Revenue '{rev_raw}' must be a valid number", raw_data=row))

            if price_val is None and rev_val is None:
                errors.append(ValidationErrorItem(row_number=row_num, field="unit_price", message="Either unit_price or revenue must be specified", raw_data=row))

        return errors

    @classmethod
    def validate_inventory_rows(
        cls,
        rows: List[Dict[str, Any]],
        known_stores: Set[str],
        known_skus: Set[str],
    ) -> List[ValidationErrorItem]:
        """Validate inventory holding records and unique store-SKU constraint."""
        errors: List[ValidationErrorItem] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for row in rows:
            row_num = row.get("_row_number", 0)
            store_code = str(row.get("store_code", "")).strip()
            sku = str(row.get("sku", "")).strip()
            qty_raw = str(row.get("stock_quantity", "")).strip()

            # Store foreign key
            if not store_code:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message="store_code cannot be empty", raw_data=row))
            elif store_code not in known_stores:
                errors.append(ValidationErrorItem(row_number=row_num, field="store_code", message=f"store_code '{store_code}' does not exist", raw_data=row))

            # SKU foreign key
            if not sku:
                errors.append(ValidationErrorItem(row_number=row_num, field="sku", message="SKU cannot be empty", raw_data=row))
            elif sku not in known_skus:
                errors.append(ValidationErrorItem(row_number=row_num, field="sku", message=f"SKU '{sku}' does not exist", raw_data=row))

            # Pair uniqueness in upload
            pair = (store_code, sku)
            if store_code and sku:
                if pair in seen_pairs:
                    errors.append(ValidationErrorItem(row_number=row_num, field="store_code+sku", message=f"Duplicate inventory record for store '{store_code}' and SKU '{sku}'", raw_data=row))
                else:
                    seen_pairs.add(pair)

            # Quantity check
            try:
                qty = int(qty_raw)
                if qty < 0:
                    errors.append(ValidationErrorItem(row_number=row_num, field="stock_quantity", message="Stock quantity must be >= 0", raw_data=row))
            except (ValueError, TypeError):
                errors.append(ValidationErrorItem(row_number=row_num, field="stock_quantity", message=f"Stock quantity '{qty_raw}' must be a valid integer", raw_data=row))

        return errors

    @classmethod
    def preview_single_csv(
        cls,
        file_bytes: bytes,
        filename: str,
        dataset_type: str,
    ) -> DatasetPreview:
        """Parse, validate, and preview a single dataset CSV file."""
        if dataset_type not in REQUIRED_COLUMNS:
            raise ValueError(f"Unsupported dataset type: '{dataset_type}'. Supported: {list(REQUIRED_COLUMNS.keys())}")

        headers, rows = cls.parse_csv_content(file_bytes)
        req_cols = REQUIRED_COLUMNS[dataset_type]
        missing_cols = req_cols - set(headers)

        errors: List[ValidationErrorItem] = []
        if missing_cols:
            errors.append(
                ValidationErrorItem(
                    row_number=1,
                    field="headers",
                    message=f"Missing required columns: {', '.join(sorted(missing_cols))}",
                    raw_data={"detected_headers": headers},
                )
            )
            return DatasetPreview(
                dataset_type=dataset_type,
                filename=filename,
                total_rows=len(rows),
                columns=headers,
                sample_rows=rows[:5],
                valid=False,
                errors=errors,
            )

        # Retrieve existing foreign key sets from DB for relationship checks
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sku FROM products")
            db_skus = {r["sku"] for r in cursor.fetchall()}
            cursor.execute("SELECT store_code FROM stores")
            db_stores = {r["store_code"] for r in cursor.fetchall()}

        if dataset_type == "products":
            errors = cls.validate_products_rows(rows)
        elif dataset_type == "stores":
            errors = cls.validate_stores_rows(rows)
        elif dataset_type == "sales":
            errors = cls.validate_sales_rows(rows, known_stores=db_stores, known_skus=db_skus)
        elif dataset_type == "inventory":
            errors = cls.validate_inventory_rows(rows, known_stores=db_stores, known_skus=db_skus)

        # Prepare clean sample rows without internal metadata
        sample_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows[:5]]

        return DatasetPreview(
            dataset_type=dataset_type,
            filename=filename,
            total_rows=len(rows),
            columns=headers,
            sample_rows=sample_rows,
            valid=len(errors) == 0,
            errors=errors,
        )

    @classmethod
    def preview_all_csv(
        cls,
        file_bytes: bytes,
        filename: str,
    ) -> CombinedPreviewResponse:
        """Parse, categorize, validate and preview combined all.csv file."""
        headers, rows = cls.parse_csv_content(file_bytes)

        if "data_type" not in headers:
            err = ValidationErrorItem(
                row_number=1,
                field="data_type",
                message="Missing required 'data_type' column in all.csv header",
                raw_data={"detected_headers": headers},
            )
            return CombinedPreviewResponse(
                filename=filename,
                total_rows=len(rows),
                datasets={},
                valid=False,
                errors=[err],
            )

        product_rows: List[Dict[str, Any]] = []
        store_rows: List[Dict[str, Any]] = []
        sale_rows: List[Dict[str, Any]] = []
        inventory_rows: List[Dict[str, Any]] = []
        type_errors: List[ValidationErrorItem] = []

        for row in rows:
            row_num = row.get("_row_number", 0)
            raw_type = str(row.get("data_type", "")).strip().lower()
            if not raw_type:
                type_errors.append(ValidationErrorItem(row_number=row_num, field="data_type", message="Row is missing 'data_type' value", raw_data=row))
            elif raw_type in ("product", "products"):
                product_rows.append(row)
            elif raw_type in ("store", "stores"):
                store_rows.append(row)
            elif raw_type in ("sale", "sales"):
                sale_rows.append(row)
            elif raw_type in ("inventory", "stock"):
                inventory_rows.append(row)
            else:
                type_errors.append(ValidationErrorItem(row_number=row_num, field="data_type", message=f"Invalid data_type '{raw_type}'. Supported: product, store, sale, inventory", raw_data=row))

        # Check existing DB keys plus any newly defined in the current batch
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sku FROM products")
            db_skus = {r["sku"] for r in cursor.fetchall()}
            cursor.execute("SELECT store_code FROM stores")
            db_stores = {r["store_code"] for r in cursor.fetchall()}

        batch_skus = {str(r.get("sku", "")).strip() for r in product_rows if str(r.get("sku", "")).strip()}
        batch_stores = {str(r.get("store_code", "")).strip() for r in store_rows if str(r.get("store_code", "")).strip()}

        all_known_skus = db_skus.union(batch_skus)
        all_known_stores = db_stores.union(batch_stores)

        p_errors = cls.validate_products_rows(product_rows) if product_rows else []
        s_errors = cls.validate_stores_rows(store_rows) if store_rows else []
        sales_errors = cls.validate_sales_rows(sale_rows, known_stores=all_known_stores, known_skus=all_known_skus) if sale_rows else []
        inv_errors = cls.validate_inventory_rows(inventory_rows, known_stores=all_known_stores, known_skus=all_known_skus) if inventory_rows else []

        all_errors = type_errors + p_errors + s_errors + sales_errors + inv_errors

        datasets = {
            "products": DatasetPreview(
                dataset_type="products",
                filename=filename,
                total_rows=len(product_rows),
                columns=[c for c in headers if c in REQUIRED_COLUMNS["products"] or c == "data_type"],
                sample_rows=[{k: v for k, v in r.items() if not k.startswith("_")} for r in product_rows[:5]],
                valid=len(p_errors) == 0,
                errors=p_errors,
            ),
            "stores": DatasetPreview(
                dataset_type="stores",
                filename=filename,
                total_rows=len(store_rows),
                columns=[c for c in headers if c in REQUIRED_COLUMNS["stores"] or c == "data_type"],
                sample_rows=[{k: v for k, v in r.items() if not k.startswith("_")} for r in store_rows[:5]],
                valid=len(s_errors) == 0,
                errors=s_errors,
            ),
            "sales": DatasetPreview(
                dataset_type="sales",
                filename=filename,
                total_rows=len(sale_rows),
                columns=[c for c in headers if c in REQUIRED_COLUMNS["sales"] or c == "data_type"],
                sample_rows=[{k: v for k, v in r.items() if not k.startswith("_")} for r in sale_rows[:5]],
                valid=len(sales_errors) == 0,
                errors=sales_errors,
            ),
            "inventory": DatasetPreview(
                dataset_type="inventory",
                filename=filename,
                total_rows=len(inventory_rows),
                columns=[c for c in headers if c in REQUIRED_COLUMNS["inventory"] or c == "data_type"],
                sample_rows=[{k: v for k, v in r.items() if not k.startswith("_")} for r in inventory_rows[:5]],
                valid=len(inv_errors) == 0,
                errors=inv_errors,
            ),
        }

        return CombinedPreviewResponse(
            filename=filename,
            total_rows=len(rows),
            datasets=datasets,
            valid=len(all_errors) == 0,
            errors=all_errors,
        )

    @classmethod
    def import_single_dataset(
        cls,
        file_bytes: bytes,
        filename: str,
        dataset_type: str,
    ) -> ImportSummaryResponse:
        """Execute single dataset import within an atomic SQLite transaction."""
        preview = cls.preview_single_csv(file_bytes, filename, dataset_type)
        if not preview.valid:
            first_err = preview.errors[0].message if preview.errors else "Validation failed"
            raise ValueError(f"Import rejected: {first_err} (Total {len(preview.errors)} error(s))")

        _, rows = cls.parse_csv_content(file_bytes)
        now_str = datetime.utcnow().isoformat()

        with get_db_connection() as conn:
            cursor = conn.cursor()

            if dataset_type == "products":
                prepared_prods = []
                for r in rows:
                    prepared_prods.append((
                        str(r.get("sku", "")).strip(),
                        str(r.get("product_name", "")).strip(),
                        str(r.get("category", "")).strip(),
                        float(r.get("unit_price", 0.0)),
                        int(r.get("reorder_level", 0)),
                    ))
                cursor.executemany(
                    """
                    INSERT INTO products (sku, product_name, category, unit_price, reorder_level)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(sku) DO UPDATE SET
                        product_name = excluded.product_name,
                        category = excluded.category,
                        unit_price = excluded.unit_price,
                        reorder_level = excluded.reorder_level
                    """,
                    prepared_prods,
                )
                counts = {"products": len(prepared_prods)}

            elif dataset_type == "stores":
                prepared_stores = []
                for r in rows:
                    prepared_stores.append((
                        str(r.get("store_code", "")).strip(),
                        str(r.get("store_name", "")).strip(),
                        str(r.get("city", "")).strip(),
                    ))
                cursor.executemany(
                    """
                    INSERT INTO stores (store_code, store_name, city)
                    VALUES (?, ?, ?)
                    ON CONFLICT(store_code) DO UPDATE SET
                        store_name = excluded.store_name,
                        city = excluded.city
                    """,
                    prepared_stores,
                )
                counts = {"stores": len(prepared_stores)}

            elif dataset_type == "sales":
                # Resolve store_code -> store_id, sku -> product_id
                cursor.execute("SELECT store_code, id FROM stores")
                store_map = {r["store_code"]: r["id"] for r in cursor.fetchall()}
                cursor.execute("SELECT sku, id FROM products")
                product_map = {r["sku"]: r["id"] for r in cursor.fetchall()}

                prepared_sales = []
                for r in rows:
                    q = int(r.get("quantity", 0))
                    p = float(r.get("unit_price", 0.0)) if str(r.get("unit_price", "")).strip() else 0.0
                    rev = float(r.get("revenue", 0.0)) if str(r.get("revenue", "")).strip() else 0.0
                    if p <= 0.0 and rev > 0.0 and q > 0:
                        p = round(rev / q, 2)
                    elif rev <= 0.0 and p > 0.0 and q > 0:
                        rev = round(p * q, 2)

                    prepared_sales.append((
                        str(r.get("sale_date", "")).strip(),
                        store_map[str(r.get("store_code", "")).strip()],
                        product_map[str(r.get("sku", "")).strip()],
                        q,
                        p,
                        rev,
                    ))

                cursor.executemany(
                    """
                    INSERT INTO sales (sale_date, store_id, product_id, quantity, unit_price, revenue)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    prepared_sales,
                )
                counts = {"sales": len(prepared_sales)}

            elif dataset_type == "inventory":
                cursor.execute("SELECT store_code, id FROM stores")
                store_map = {r["store_code"]: r["id"] for r in cursor.fetchall()}
                cursor.execute("SELECT sku, id FROM products")
                product_map = {r["sku"]: r["id"] for r in cursor.fetchall()}

                prepared_inv = []
                for r in rows:
                    prepared_inv.append((
                        store_map[str(r.get("store_code", "")).strip()],
                        product_map[str(r.get("sku", "")).strip()],
                        int(r.get("stock_quantity", 0)),
                    ))

                cursor.executemany(
                    """
                    INSERT INTO inventory (store_id, product_id, stock_quantity)
                    VALUES (?, ?, ?)
                    ON CONFLICT(store_id, product_id) DO UPDATE SET
                        stock_quantity = excluded.stock_quantity,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    prepared_inv,
                )
                counts = {"inventory": len(prepared_inv)}

        # Increment authoritative data version to invalidate previous Copilot caches
        DataVersionService.increment_data_version()

        return ImportSummaryResponse(
            success=True,
            message=f"Successfully imported {dataset_type} dataset.",
            imported_counts=counts,
            timestamp=now_str,
        )

    @classmethod
    def import_all_combined(
        cls,
        file_bytes: bytes,
        filename: str,
    ) -> ImportSummaryResponse:
        """Execute atomic multi-dataset import from combined all.csv."""
        preview = cls.preview_all_csv(file_bytes, filename)
        if not preview.valid:
            first_err = preview.errors[0].message if preview.errors else "Validation failed"
            raise ValueError(f"Combined import rejected: {first_err} (Total {len(preview.errors)} error(s))")

        _, rows = cls.parse_csv_content(file_bytes)
        now_str = datetime.utcnow().isoformat()

        product_rows = [r for r in rows if str(r.get("data_type", "")).strip().lower() in ("product", "products")]
        store_rows = [r for r in rows if str(r.get("data_type", "")).strip().lower() in ("store", "stores")]
        sale_rows = [r for r in rows if str(r.get("data_type", "")).strip().lower() in ("sale", "sales")]
        inventory_rows = [r for r in rows if str(r.get("data_type", "")).strip().lower() in ("inventory", "stock")]

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Insert Products
            if product_rows:
                prepared_prods = []
                for r in product_rows:
                    prepared_prods.append((
                        str(r.get("sku", "")).strip(),
                        str(r.get("product_name", "")).strip(),
                        str(r.get("category", "")).strip(),
                        float(r.get("unit_price", 0.0)),
                        int(r.get("reorder_level", 0)),
                    ))
                cursor.executemany(
                    """
                    INSERT INTO products (sku, product_name, category, unit_price, reorder_level)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(sku) DO UPDATE SET
                        product_name = excluded.product_name,
                        category = excluded.category,
                        unit_price = excluded.unit_price,
                        reorder_level = excluded.reorder_level
                    """,
                    prepared_prods,
                )

            # 2. Insert Stores
            if store_rows:
                prepared_stores = []
                for r in store_rows:
                    prepared_stores.append((
                        str(r.get("store_code", "")).strip(),
                        str(r.get("store_name", "")).strip(),
                        str(r.get("city", "")).strip(),
                    ))
                cursor.executemany(
                    """
                    INSERT INTO stores (store_code, store_name, city)
                    VALUES (?, ?, ?)
                    ON CONFLICT(store_code) DO UPDATE SET
                        store_name = excluded.store_name,
                        city = excluded.city
                    """,
                    prepared_stores,
                )

            # 3. Build ID mappings
            cursor.execute("SELECT store_code, id FROM stores")
            store_map = {r["store_code"]: r["id"] for r in cursor.fetchall()}
            cursor.execute("SELECT sku, id FROM products")
            product_map = {r["sku"]: r["id"] for r in cursor.fetchall()}

            # 4. Insert Sales
            if sale_rows:
                prepared_sales = []
                for r in sale_rows:
                    q = int(r.get("quantity", 0))
                    p = float(r.get("unit_price", 0.0)) if str(r.get("unit_price", "")).strip() else 0.0
                    rev = float(r.get("revenue", 0.0)) if str(r.get("revenue", "")).strip() else 0.0
                    if p <= 0.0 and rev > 0.0 and q > 0:
                        p = round(rev / q, 2)
                    elif rev <= 0.0 and p > 0.0 and q > 0:
                        rev = round(p * q, 2)

                    prepared_sales.append((
                        str(r.get("sale_date", "")).strip(),
                        store_map[str(r.get("store_code", "")).strip()],
                        product_map[str(r.get("sku", "")).strip()],
                        q,
                        p,
                        rev,
                    ))
                cursor.executemany(
                    """
                    INSERT INTO sales (sale_date, store_id, product_id, quantity, unit_price, revenue)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    prepared_sales,
                )

            # 5. Insert Inventory
            if inventory_rows:
                prepared_inv = []
                for r in inventory_rows:
                    prepared_inv.append((
                        store_map[str(r.get("store_code", "")).strip()],
                        product_map[str(r.get("sku", "")).strip()],
                        int(r.get("stock_quantity", 0)),
                    ))
                cursor.executemany(
                    """
                    INSERT INTO inventory (store_id, product_id, stock_quantity)
                    VALUES (?, ?, ?)
                    ON CONFLICT(store_id, product_id) DO UPDATE SET
                        stock_quantity = excluded.stock_quantity,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    prepared_inv,
                )

        # Increment authoritative data version to invalidate previous Copilot caches
        DataVersionService.increment_data_version()

        counts = {
            "products": len(product_rows),
            "stores": len(store_rows),
            "sales": len(sale_rows),
            "inventory": len(inventory_rows),
        }

        return ImportSummaryResponse(
            success=True,
            message=f"All datasets in '{filename}' were successfully imported in a single atomic transaction.",
            imported_counts=counts,
            timestamp=now_str,
        )

    @staticmethod
    def get_template(template_name: str) -> Tuple[str, str]:
        """Return CSV template filename and string content."""
        clean_name = template_name.strip().lower()
        if clean_name in ("products", "products.csv"):
            filename = "products_template.csv"
            content = "sku,product_name,category,unit_price,reorder_level\nP001,Wireless Optical Mouse,Electronics,799,20\nP002,Bluetooth Ergonomic Keyboard,Electronics,1499,15\nP003,USB-C Fast Charging Cable 2m,Accessories,299,30\n"
        elif clean_name in ("stores", "stores.csv"):
            filename = "stores_template.csv"
            content = "store_code,store_name,city\nSTR-001,RetailCo Chennai Central,Chennai\nSTR-002,RetailCo Anna Nagar,Chennai\nSTR-003,RetailCo Velachery,Chennai\n"
        elif clean_name in ("sales", "sales.csv"):
            filename = "sales_template.csv"
            content = "sale_date,store_code,sku,quantity,unit_price,revenue\n2026-08-20,STR-001,P001,15,799,11985\n2026-08-20,STR-001,P002,8,1499,11992\n2026-08-21,STR-002,P001,10,799,7990\n"
        elif clean_name in ("inventory", "inventory.csv"):
            filename = "inventory_template.csv"
            content = "store_code,sku,stock_quantity\nSTR-001,P001,45\nSTR-001,P002,32\nSTR-002,P001,12\n"
        elif clean_name in ("all", "all.csv"):
            filename = "all_template.csv"
            content = (
                "data_type,sku,product_name,category,unit_price,reorder_level,store_code,store_name,city,sale_date,quantity,revenue,stock_quantity\n"
                "product,P001,Wireless Optical Mouse,Electronics,799,20,,,,,,,\n"
                "product,P002,Bluetooth Ergonomic Keyboard,Electronics,1499,15,,,,,,,\n"
                "store,,,,,,STR-001,RetailCo Chennai Central,Chennai,,,,\n"
                "store,,,,,,STR-002,RetailCo Anna Nagar,Chennai,,,,\n"
                "sale,P001,,,,,STR-001,,,2026-08-20,15,11985,\n"
                "inventory,P001,,,,,STR-001,,,,,45\n"
            )
        else:
            raise ValueError(f"Unknown template '{template_name}'. Available: products, stores, sales, inventory, all")

        return filename, content

    @staticmethod
    def reset_demo_data() -> ImportSummaryResponse:
        """Reset the SQLite database back to the standard seeded demo dataset."""
        counts = seed_database(force=True)
        DataVersionService.increment_data_version()
        return ImportSummaryResponse(
            success=True,
            message="Database successfully reset to the original seeded synthetic demo dataset.",
            imported_counts=counts,
            timestamp=datetime.utcnow().isoformat(),
        )
