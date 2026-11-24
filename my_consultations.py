def booking_consultation():
        


        import re
        import sqlite3
        from datetime import datetime, time, timedelta
        import pandas as pd
        import requests
        import streamlit as st
        import streamlit.components.v1 as components

        # -----------------------------------------------------------------------------
        # Database Setup
        # -----------------------------------------------------------------------------
        DB_FILE = "consultations.db"


        def init_sqlite_db():
            """Initialize SQLite database for storing EVM consultation bookings."""
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    service_type TEXT NOT NULL,
                    booking_date TEXT NOT NULL,
                    booking_time TEXT NOT NULL,
                    portfolio_size TEXT,
                    trading_experience TEXT,
                    consultation_topics TEXT,
                    notes TEXT,
                    payment_network TEXT,
                    payment_currency TEXT,
                    amount_usd REAL,
                    tx_hash TEXT UNIQUE NOT NULL,
                    tx_status TEXT DEFAULT 'Pending Verification',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
            conn.close()


        def save_booking(data):
            """Save verified client booking into database."""
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO bookings (
                        client_name, email, phone, service_type,
                        booking_date, booking_time, portfolio_size,
                        trading_experience, consultation_topics, notes,
                        payment_network, payment_currency, amount_usd, tx_hash, tx_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data["name"],
                        data["email"],
                        data["phone"],
                        data["service"],
                        data["date"].strftime("%Y-%m-%d"),
                        data["time"].strftime("%H:%M"),
                        data["portfolio_size"],
                        data["trading_experience"],
                        ", ".join(data["topics"]),
                        data["notes"],
                        data["payment_network"],
                        data["payment_currency"],
                        data["amount_usd"],
                        data["tx_hash"],
                        data["tx_status"],
                    ),
                )
                conn.commit()
                success = True
                msg = "Booking successfully registered!"
            except sqlite3.IntegrityError:
                success = False
                msg = "⚠️ This Transaction Hash has already been submitted for a previous booking."
            finally:
                conn.close()

            return success, msg


        def get_existing_bookings(selected_date):
            """Retrieve booked time slots for a given date."""
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT booking_time FROM bookings WHERE booking_date = ?",
                (selected_date.strftime("%Y-%m-%d"),),
            )
            booked_slots = [row[0] for row in cursor.fetchall()]
            conn.close()
            return booked_slots


        # -----------------------------------------------------------------------------
        # On-Chain RPC Verification (EVM Only)
        # -----------------------------------------------------------------------------
        def verify_tx_onchain(tx_hash, network):
            """Format regex check and live RPC query for EVM networks."""
            tx_hash = tx_hash.strip()

            # EVM transaction hash format check (0x followed by 64 hex chars)
            if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
                return False, "Invalid EVM transaction hash format (must start with '0x')."

            try:
                rpc_urls = {
                    "ETHEREUM": "https://cloudflare-eth.com",
                    "BNB CHAIN": "https://bsc-dataseed.binance.org",
                    "POLYGON": "https://polygon-rpc.com",
                    "BASE": "https://mainnet.base.org",
                    "OPTIMISM": "https://mainnet.optimism.io",
                    "AVALANCHE": "https://api.avax.network/ext/bc/C/rpc",
                }
                rpc = rpc_urls.get(network, "https://cloudflare-eth.com")
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                    "id": 1,
                }
                res = requests.post(rpc, json=payload, timeout=5)
                data = res.json()
                receipt = data.get("result")
                if receipt:
                    if receipt.get("status") == "0x1":
                        return True, f"Transaction Confirmed on {network}"
                    return False, "Transaction executed but FAILED on-chain."
                return True, "Hash format valid (Broadcasted / Pending Mining)"

            except Exception:
                return True, "Hash format valid (RPC node connection timed out)"


        # -----------------------------------------------------------------------------
        # Main Application
        # -----------------------------------------------------------------------------
        def main():
            st.set_page_config(
                page_title="Crypto Advisory & Booking",
                page_icon="📈",
                layout="wide",
            )

            init_sqlite_db()

            # Sidebar: Admin Dashboard
            st.sidebar.title("📈 Open Cipher Consults")
            admin_mode = st.sidebar.checkbox("Admin Dashboard")

            if admin_mode:
                admin_password = st.sidebar.text_input("Admin Password", type="password")
                if admin_password == "cipher2026":
                    st.title("🛡️ Scheduled Consultations & Payments")
                    conn = sqlite3.connect(DB_FILE)
                    df = pd.read_sql_query("SELECT * FROM bookings ORDER BY id DESC", conn)
                    conn.close()

                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "Download CSV Ledger",
                            csv,
                            "consultation_bookings.csv",
                            "text/csv",
                        )
                    else:
                        st.info("No bookings recorded yet.")
                else:
                    st.sidebar.error("Invalid Admin Key")
                return

            st.title("📅 Book a Consultation")

            col1, col2 = st.columns([1, 1], gap="large")

            # Column 1: Service & Schedule
            with col1:
                st.markdown("### 1. Select Consultation & Schedule")

                services = {
                    "Crypto Market Analysis & Strategy (45 min)": 150,
                    "Quantitative Trading & Algo Setup (60 min)": 250,
                    "Portfolio Risk Audit & DeFi Advisory (60 min)": 200,
                }

                selected_service = st.selectbox("Consultation Type", list(services.keys()))
                service_price = services[selected_service]
                st.info(f"**Fee:** ${service_price} USD")

                today = datetime.now().date()
                max_date = today + timedelta(days=30)
                booking_date = st.date_input("Choose Date", min_value=today, max_value=max_date)

                all_slots = [time(9, 0), time(10, 30), time(13, 0), time(14, 30), time(16, 0)]
                booked_times = get_existing_bookings(booking_date)
                available_slots = [t for t in all_slots if t.strftime("%H:%M") not in booked_times]

                if available_slots:
                    booking_time = st.selectbox(
                        "Available Time Slot (EAT)",
                        available_slots,
                        format_func=lambda x: x.strftime("%I:%M %p"),
                    )
                else:
                    st.error("No slots available on this date.")
                    booking_time = None

                st.markdown("---")
                st.markdown("### 2. Client Details")
                client_name = st.text_input("Full Name *")
                email = st.text_input("Email Address *")
                phone = st.text_input("Phone Number / Telegram Handle")

                portfolio_size = st.selectbox(
                    "Approximate Portfolio Size",
                    ["< $10k", "$10k - $50k", "$50k - $250k", "$250k+"],
                )

                trading_exp = st.select_slider(
                    "Trading Experience Level",
                    options=["Beginner", "Intermediate", "Advanced", "Institutional"],
                )

                topics = st.multiselect(
                    "Primary Topics to Cover",
                    [
                        "Technical Analysis (Elliott Wave / Wyckoff)",
                        "Automated Trading & Execution APIs",
                        "Perpetuals & Derivatives Strategy",
                        "DeFi Liquidity Provisioning",
                        "Risk Management & Hedging",
                    ],
                )
                notes = st.text_area("Specific Goals for the Session")

            # Column 2: Payment & Proof
            with col2:
                st.markdown("### 3. Payment & Transaction Proof")

                # Solana removed; strictly EVM network options remain
                network_payment_options = {
                    "BNB CHAIN": ["BUSD"],
                    "BASE": ["USDBC"],
                    "POLYGON": ["USDC", "DAI", "USDT"],
                    "OPTIMISM": ["USDC"],
                    "AVALANCHE": ["EUROC"],
                    "ETHEREUM": ["USDC"],
                }

                network_options = list(network_payment_options.keys())
                selected_network = st.selectbox("Choose Network:", network_options)
                payment_options = network_payment_options.get(selected_network, [])

                if payment_options:
                    selected_payment_option = st.selectbox("Choose Settlement Token:", payment_options)

                    # Standard EVM Deposit Address
                    receiver_address = "0x1560fE2D29b86a0B0040e96545bDe4531E3feBD3"

                    st.write(f"**Amount Due:** ${service_price} USD")

                    # PIP Button Component
                    html_code = f"""
                    <div style="display: flex; flex-direction: column; align-items: center; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0;">
                        <script src="https://button.getpip.com/cdn/pipbutton.js"></script>
                        <div class="pip-button"
                            data-amount="{service_price}"
                            data-chainNetwork="{selected_network}"
                            data-currency="{selected_payment_option}"
                            data-label="PAY WITH CRYPTO"
                            data-useLabel="true"
                            data-receiver="{receiver_address}"
                            data-buttonColor="#1149FF"
                            data-buttonTextColor="#FFFFFF"
                            data-memo="{receiver_address}">
                        </div>
                        <p style="margin-top: 10px; font-size: 11px; color: #6c757d; text-align: center;">
                            Deposit EVM Address: <br><code>{receiver_address}</code>
                        </p>
                    </div>
                    """
                    components.html(html_code, height=180)

                    st.markdown("#### 4. Confirm Payment")
                    tx_hash_input = st.text_input(
                        "Transaction Hash *",
                        placeholder="Paste EVM Tx Hash (starts with 0x...)",
                        help="Copy and paste the transaction hash generated by your wallet after completing the transfer.",
                    )

                    # Submit and Verify Action
                    if st.button("Submit Booking & Verify Proof"):
                        if not client_name or not email:
                            st.error("Please provide your Name and Email.")
                        elif not booking_time:
                            st.error("Please pick an available time slot.")
                        elif not tx_hash_input.strip():
                            st.error("Please paste your Transaction Hash proof.")
                        else:
                            is_valid_format, verify_msg = verify_tx_onchain(tx_hash_input, selected_network)

                            if not is_valid_format:
                                st.error(f"❌ Verification Failed: {verify_msg}")
                            else:
                                booking_payload = {
                                    "name": client_name,
                                    "email": email,
                                    "phone": phone,
                                    "service": selected_service,
                                    "date": booking_date,
                                    "time": booking_time,
                                    "portfolio_size": portfolio_size,
                                    "trading_experience": trading_exp,
                                    "topics": topics,
                                    "notes": notes,
                                    "payment_network": selected_network,
                                    "payment_currency": selected_payment_option,
                                    "amount_usd": service_price,
                                    "tx_hash": tx_hash_input.strip(),
                                    "tx_status": verify_msg,
                                }

                                saved, db_msg = save_booking(booking_payload)
                                if saved:
                                    st.success("✅ Payment verified & consultation scheduled!")
                                    st.balloons()
                                    st.markdown(
                                        f"""
                                    **Booking Summary:**
                                    * **Tx Hash:** `{tx_hash_input.strip()}`
                                    * **Status:** {verify_msg}
                                    * **Service:** {selected_service}
                                    * **Date:** {booking_date.strftime('%B %d, %Y')} at {booking_time.strftime('%I:%M %p')} EAT
                                    """
                                    )
                                else:
                                    st.error(db_msg)


#trx hash: 0x5e57dae5016332ac023c9243b557705c62847e4243086b6f6093b12273801ce3

#RUN COMMAND : streamlit run my_consultations.py



import re
import sqlite3
from datetime import datetime, time, timedelta
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

DB_FILE = "consultations.db"


def init_sqlite_db():
    """Initialize SQLite database for storing EVM consultation bookings."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service_type TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            portfolio_size TEXT,
            trading_experience TEXT,
            consultation_topics TEXT,
            notes TEXT,
            payment_network TEXT,
            payment_currency TEXT,
            amount_usd REAL,
            tx_hash TEXT UNIQUE NOT NULL,
            tx_status TEXT DEFAULT 'Pending Verification',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def save_booking(data):
    """Save verified client booking into database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO bookings (
                client_name, email, phone, service_type,
                booking_date, booking_time, portfolio_size,
                trading_experience, consultation_topics, notes,
                payment_network, payment_currency, amount_usd, tx_hash, tx_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                data["email"],
                data["phone"],
                data["service"],
                data["date"].strftime("%Y-%m-%d"),
                data["time"].strftime("%H:%M"),
                data["portfolio_size"],
                data["trading_experience"],
                ", ".join(data["topics"]),
                data["notes"],
                data["payment_network"],
                data["payment_currency"],
                data["amount_usd"],
                data["tx_hash"],
                data["tx_status"],
            ),
        )
        conn.commit()
        success = True
        msg = "Booking successfully registered!"
    except sqlite3.IntegrityError:
        success = False
        msg = "⚠️ This Transaction Hash has already been submitted for a previous booking."
    finally:
        conn.close()

    return success, msg


def get_existing_bookings(selected_date):
    """Retrieve booked time slots for a given date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT booking_time FROM bookings WHERE booking_date = ?",
        (selected_date.strftime("%Y-%m-%d"),),
    )
    booked_slots = [row[0] for row in cursor.fetchall()]
    conn.close()
    return booked_slots


import json
import requests

RECIPIENT_WALLET = "0x1560fE2D29b86a0B0040e96545bDe4531E3feBD3".lower()
TRANSFER_EVENT_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


def verify_tx_onchain(tx_hash, network, expected_usd_amount=None, token_decimals=6):
    """Verify EVM transaction format, on-chain execution, recipient wallet, and payment amount."""
    tx_hash = tx_hash.strip()

    # 1. Format check
    if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid EVM transaction hash format (must start with '0x')."

    rpc_urls = {
        "ETHEREUM": "https://cloudflare-eth.com",
        "BNB CHAIN": "https://bsc-dataseed.binance.org",
        "POLYGON": "https://polygon-rpc.com",
        "BASE": "https://mainnet.base.org",
        "OPTIMISM": "https://mainnet.optimism.io",
        "AVALANCHE": "https://api.avax.network/ext/bc/C/rpc",
    }
    rpc = rpc_urls.get(network.upper(), "https://cloudflare-eth.com")
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionReceipt",
        "params": [tx_hash],
        "id": 1,
    }

    try:
        res = requests.post(rpc, json=payload, timeout=8)
        data = res.json()
        receipt = data.get("result")

        # FIX: Do not auto-approve missing receipts or RPC errors
        if not receipt:
            return (
                False,
                "Transaction not found on-chain. Please ensure the hash is correct and mined.",
            )

        if receipt.get("status") != "0x1":
            return False, "Transaction executed but FAILED on-chain."

        # Optional: Inspect ERC-20 transfer logs if expected_usd_amount is provided
        if expected_usd_amount:
            padded_recipient = f"0x{RECIPIENT_WALLET.replace('0x', '').zfill(64)}"
            payment_found = False
            amount_transferred = 0.0

            for log in receipt.get("logs", []):
                topics = log.get("topics", [])
                if (
                    len(topics) >= 3
                    and topics[0].lower() == TRANSFER_EVENT_TOPIC.lower()
                    and topics[2].lower() == padded_recipient.lower()
                ):
                    raw_val = int(log.get("data", "0x0"), 16)
                    amount_transferred = raw_val / (10**token_decimals)
                    payment_found = True
                    break

            if not payment_found:
                return (
                    False,
                    f"Transaction succeeded, but no payment was sent to {RECIPIENT_WALLET}.",
                )

            if amount_transferred < (expected_usd_amount * 0.99):
                return (
                    False,
                    f"Insufficient payment amount: received {amount_transferred:.2f}, expected {expected_usd_amount:.2f}.",
                )

        return True, f"Transaction confirmed on {network}"

    except Exception as e:
        return False, f"RPC Network Error: Could not verify transaction ({str(e)})"


import json
import re
import urllib.request


def rpc_post(rpc_url: str, method: str, params: list) -> dict:
    """Send a JSON-RPC request to an EVM RPC node using urllib."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        rpc_url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def verify_evm_payment(
    rpc_url: str,
    tx_hash: str,
    expected_wallet: str,
    expected_amount_usd: float,
    token_decimals: int = 6,
) -> tuple[bool, str]:
    """Verify an EVM ERC-20 token transfer transaction on-chain."""
    # 1. Validate Tx Hash Format
    if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid EVM transaction hash format."

    try:
        # 2. Fetch Transaction Receipt
        res = rpc_post(rpc_url, "eth_getTransactionReceipt", [tx_hash])
        receipt = res.get("result")

        if not receipt:
            return (
                False,
                "Transaction receipt not found or still pending in mempool.",
            )

        # 3. Check Execution Status (0x1 = Success, 0x0 = Reverted)
        status = receipt.get("status")
        if status != "0x1":
            return False, "Transaction was reverted or failed on-chain."

        # ERC-20 Transfer Event Topic 0: Transfer(address,address,uint256)
        TRANSFER_EVENT_TOPIC = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        # Normalize expected wallet address to padded 32-byte topic standard
        clean_expected_wallet = expected_wallet.lower().replace("0x", "")
        padded_expected_wallet = (
            f"0x{clean_expected_wallet.zfill(64)}".lower()
        )

        valid_transfer_found = False
        amount_transferred = 0.0

        # 4. Scan Event Logs for ERC-20 Transfer to expected_wallet
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if len(topics) >= 3:
                event_sig = topics[0].lower()
                recipient_topic = topics[2].lower()

                if (
                    event_sig == TRANSFER_EVENT_TOPIC
                    and recipient_topic == padded_expected_wallet
                ):
                    data_hex = log.get("data", "0x0")
                    if data_hex == "0x":
                        raw_value = 0
                    else:
                        raw_value = int(data_hex, 16)

                    # Scale raw token integer by token decimals
                    amount_transferred = raw_value / (10**token_decimals)
                    valid_transfer_found = True
                    break

        if not valid_transfer_found:
            return (
                False,
                f"Transaction did not contain an ERC-20 transfer to receiver {expected_wallet}.",
            )

        # 5. Check Received Amount satisfies required fee (1% tolerance for slippage/fees)
        if amount_transferred < (expected_amount_usd * 0.99):
            return (
                False,
                f"Insufficient transfer amount: received {amount_transferred:.2f}, required {expected_amount_usd:.2f}.",
            )

        return (
            True,
            f"Verified successfully! Transfer of {amount_transferred:.2f} tokens confirmed.",
        )

    except Exception as e:
        return False, f"RPC Verification Error: {str(e)}"





from datetime import datetime, time, timedelta
import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def booking_consultation():
    init_sqlite_db()

    # Admin View Toggle
    admin_mode = st.sidebar.checkbox("Admin Dashboard")

    if admin_mode:
        admin_password = st.sidebar.text_input(
            "Admin Password", type="password"
        )
        if admin_password == "cipher2026":
            st.markdown("### 🛡️ Scheduled Consultations & Payments")
            conn = sqlite3.connect(DB_FILE)
            df = pd.read_sql_query(
                "SELECT * FROM bookings ORDER BY id DESC", conn
            )
            conn.close()

            if not df.empty:
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download CSV Ledger",
                    csv,
                    "consultation_bookings.csv",
                    "text/csv",
                )
            else:
                st.info("No bookings recorded yet.")
        else:
            st.sidebar.error("Invalid Admin Key")
        return

    # WRAP EVERYTHING IN A FORM TO PRESERVE STATE
    with st.form("booking_form", clear_on_submit=False):
        col1, col2 = st.columns([1, 1], gap="large")

        # Column 1: Service & Schedule
        with col1:
            st.markdown("### 1. Select Consultation & Schedule")

            services = {
                "Crypto Market Analysis & Strategy (45 min)": 150,
                "Trading Psychology & Risk Management (45 min)": 100,
                "Quantitative Trading & Algo Setup (60 min)": 250,
                "Portfolio Risk Audit & DeFi Advisory (60 min)": 200,
            }

            selected_service = st.selectbox(
                "Consultation Type", list(services.keys())
            )
            service_price = services[selected_service]
            st.info(f"**Fee:** ${service_price} USD")

            today = datetime.now().date()
            max_date = today + timedelta(days=30)
            booking_date = st.date_input(
                "Choose Date", min_value=today, max_value=max_date
            )

            all_slots = [
                time(9, 0),
                time(10, 30),
                time(13, 0),
                time(14, 30),
                time(16, 0),
            ]
            booked_times = get_existing_bookings(booking_date)
            available_slots = [
                t for t in all_slots if t.strftime("%H:%M") not in booked_times
            ]

            if available_slots:
                booking_time = st.selectbox(
                    "Available Time Slot (EAT)",
                    available_slots,
                    format_func=lambda x: x.strftime("%I:%M %p"),
                )
            else:
                st.error("No slots available on this date.")
                booking_time = None

            st.markdown("---")
            st.markdown("### 2. Client Details")
            client_name = st.text_input("Full Name *", key="client_name_input")
            email = st.text_input("Email Address *", key="email_input")
            phone = st.text_input("Phone Number / Telegram Handle")

            portfolio_size = st.selectbox(
                "Approximate Portfolio Size",
                ["< $10k", "$10k - $50k", "$50k - $250k", "$250k+"],
            )

            trading_exp = st.select_slider(
                "Trading Experience Level",
                options=[
                    "Beginner",
                    "Intermediate",
                    "Advanced",
                    "Institutional",
                ],
            )

            topics = st.multiselect(
                "Primary Topics to Cover",
                [
                    "Technical Analysis (Elliott Wave / Wyckoff)",
                    "Automated Trading & Execution APIs",
                    "Perpetuals & Derivatives Strategy",
                    "DeFi Liquidity Provisioning",
                    "Risk Management & Hedging",
                    "Trading Psychology & Risk Management",
                ],
            )
            notes = st.text_area("Specific Goals for the Session")

        # Column 2: Payment & Proof
        with col2:
            st.markdown("### 3. Payment & Transaction Proof")

            network_payment_options = {
                "BNB CHAIN": ["BUSD", "USDT", "USDC"],
                "BASE": ["USDBC", "USDC"],
                "POLYGON": ["USDC", "DAI", "USDT"],
                "OPTIMISM": ["USDC", "USDT"],
                "AVALANCHE": ["EUROC", "USDC", "USDT"],
                "ETHEREUM": ["USDC", "USDT", "DAI"],
            }

            network_options = list(network_payment_options.keys())
            selected_network = st.selectbox("Choose Network:", network_options)
            payment_options = network_payment_options.get(selected_network, [])

            if payment_options:
                selected_payment_option = st.selectbox(
                    "Choose Settlement Token:", payment_options
                )
                receiver_address = "0x1560fE2D29b86a0B0040e96545bDe4531E3feBD3"

                st.write(f"**Amount Due:** ${service_price} USD")

                html_code = f"""
                <div style="display: flex; flex-direction: column; align-items: center; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0;">
                    <script src="https://button.getpip.com/cdn/pipbutton.js"></script>
                    <div class="pip-button"
                        data-amount="{service_price}"
                        data-chainNetwork="{selected_network}"
                        data-currency="{selected_payment_option}"
                        data-label="PAY WITH CRYPTO"
                        data-useLabel="true"
                        data-receiver="{receiver_address}"
                        data-buttonColor="#1149FF"
                        data-buttonTextColor="#FFFFFF"
                        data-memo="{receiver_address}">
                    </div>
                    <p style="margin-top: 10px; font-size: 11px; color: #6c757d; text-align: center;">
                        Deposit EVM Address: <br><code>{receiver_address}</code>
                    </p>
                </div>
                """
                components.html(html_code, height=180)

                st.markdown("#### 4. Confirm Payment")
                tx_hash_input = st.text_input(
                    "Transaction Hash *",
                    placeholder="Paste EVM Tx Hash (starts with 0x...)",
                    help="Copy and paste the transaction hash generated by your wallet after completing the transfer.",
                    key="tx_hash_input",
                )

                # Submit Form Button
                submitted = st.form_submit_button(
                    "Submit Booking & Verify Proof"
                )

                if submitted:
                    if not client_name.strip() or not email.strip():
                        st.error("Please provide your Name and Email.")
                    elif not booking_time:
                        st.error("Please pick an available time slot.")
                    elif not tx_hash_input.strip():
                        st.error("Please paste your Transaction Hash proof.")
                    else:
                        # Map networks to fast public RPC endpoints
                        rpc_endpoints = {
                            "ETHEREUM": "https://eth.llamarpc.com",
                            "BNB CHAIN": "https://binance.llamarpc.com",
                            "POLYGON": "https://polygon.llamarpc.com",
                            "BASE": "https://mainnet.base.org",
                            "OPTIMISM": "https://mainnet.optimism.io",
                            "AVALANCHE": "https://api.avax.network/ext/bc/C/rpc",
                        }
                        rpc_url = rpc_endpoints.get(
                            selected_network.upper(), "https://eth.llamarpc.com"
                        )

                        # Determine token decimal standards (USDC/USDT/USDBC/EUROC = 6, DAI/BUSD = 18)
                        token_decimals = (
                            6
                            if selected_payment_option
                            in ["USDC", "USDT", "USDBC", "EUROC"]
                            else 18
                        )

                        with st.spinner("Verifying payment on-chain..."):
                            is_valid, verify_msg = verify_evm_payment(
                                rpc_url=rpc_url,
                                tx_hash=tx_hash_input.strip(),
                                expected_wallet=receiver_address,
                                expected_amount_usd=float(service_price),
                                token_decimals=token_decimals,
                            )

                        if not is_valid:
                            st.error(f"❌ Payment Verification Failed: {verify_msg}")
                        else:
                            booking_payload = {
                                "name": client_name.strip(),
                                "email": email.strip(),
                                "phone": phone.strip(),
                                "service": selected_service,
                                "date": booking_date,
                                "time": booking_time,
                                "portfolio_size": portfolio_size,
                                "trading_experience": trading_exp,
                                "topics": topics,
                                "notes": notes,
                                "payment_network": selected_network,
                                "payment_currency": selected_payment_option,
                                "amount_usd": service_price,
                                "tx_hash": tx_hash_input.strip(),
                                "tx_status": "Verified On-Chain",
                            }

                            saved, db_msg = save_booking(booking_payload)
                            if saved:
                                st.success(
                                    "✅ Payment verified & consultation scheduled!"
                                )
                                st.balloons()
                                st.markdown(
                                    f"""
                                **Booking Summary:**
                                * **Tx Hash:** `{tx_hash_input.strip()}`
                                * **Status:** Verified On-Chain
                                * **Service:** {selected_service}
                                * **Date:** {booking_date.strftime('%B %d, %Y')} at {booking_time.strftime('%I:%M %p')} EAT
                                """
                                )
                            else:
                                st.error(db_msg)



