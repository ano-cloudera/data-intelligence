from __future__ import annotations


def build_database_description() -> str:
    return (
        "Database purpose: This is a banking demo dataset for customer, deposit, credit, and fraud analytics."
    )


def build_table_descriptions() -> str:
    return """
Table: customers
- Business meaning: customer master/profile data
- Grain: one row per customer
- Columns:
  - customer_id: unique customer identifier
  - full_name: customer full name
  - birth_date: customer date of birth stored as string
  - city: customer city
  - segment: customer segment/category
  - join_date: customer onboarding/join date stored as string

Table: deposits
- Business meaning: customer deposit account data
- Grain: one row per deposit account
- Columns:
  - account_id: unique deposit account identifier
  - customer_id: foreign key to customers.customer_id
  - product_type: deposit product/category
  - balance: deposit balance amount
  - maturity_date: deposit maturity date stored as string
  - branch_code: branch identifier/code
  - status: deposit/account status

Table: credits
- Business meaning: customer credit or loan account data
- Grain: one row per credit account
- Columns:
  - credit_id: unique credit account identifier
  - customer_id: foreign key to customers.customer_id
  - credit_type: credit product/category
  - principal_amount: original approved credit amount
  - outstanding_balance: current unpaid balance
  - interest_rate: annual credit interest rate percentage
  - disbursement_date: credit disbursement date stored as string
  - maturity_date: credit maturity date stored as string
  - collectibility: credit quality bucket
  - branch_code: branch identifier/code
  - status: credit/account lifecycle status

Table: fraud_transactions
- Business meaning: transaction-level fraud monitoring and investigation data
- Grain: one row per transaction
- Columns:
  - transaction_id: unique transaction identifier
  - customer_id: foreign key to customers.customer_id
  - account_id: related deposit account identifier when available
  - transaction_timestamp: transaction timestamp stored as string
  - transaction_date: transaction date stored as string
  - transaction_type: transaction category such as transfer or card payment
  - channel: transaction channel such as mobile_app, atm, branch, internet_banking, or edc
  - amount: transaction amount
  - currency_code: transaction currency code
  - merchant_category: merchant or payee category
  - merchant_name: merchant or payee name
  - origin_city: customer home or origin city
  - destination_city: destination city or receiving city
  - origin_branch_code: branch identifier associated with the customer origin
  - device_id: device identifier used for the transaction
  - device_os: device or terminal operating system/type
  - ip_address: originating IP address string
  - network_type: network type used by the transaction channel
  - is_new_device: indicator that the device is new for the customer
  - is_foreign_ip: indicator that the IP is outside the customer's normal profile
  - customer_segment: customer segment copied from the customer profile
  - customer_age: customer age at transaction time
  - account_tenure_days: customer tenure in days at transaction time
  - days_since_last_txn: days since the customer's previous transaction
  - txn_count_1d: transaction count in the prior 1-day window including the current transaction
  - txn_count_7d: transaction count in the prior 7-day window including the current transaction
  - txn_amount_1d: transaction amount in the prior 1-day window including the current transaction
  - txn_amount_7d: transaction amount in the prior 7-day window including the current transaction
  - avg_txn_amount_30d: average transaction amount over the recent 30-day history
  - amount_vs_avg_30d_ratio: current amount divided by recent 30-day average
  - is_round_amount: indicator for round-number transaction amounts
  - is_night_txn: indicator for night-time transactions
  - is_weekend_txn: indicator for weekend transactions
  - failed_login_count_24h: failed login count in the last 24 hours
  - beneficiary_bank: receiving or beneficiary bank
  - beneficiary_account_age_days: beneficiary account age in days
  - is_new_beneficiary: indicator that the beneficiary is new for the customer
  - distance_from_home_km: estimated transaction distance from the customer home city
  - velocity_risk_score: rule-based risk score focused on transaction velocity
  - behavioral_risk_score: rule-based risk score focused on behavior change
  - fraud_flag: fraud target label where 1 means fraud
  - fraud_reason: explainability reason for the fraud or legitimate label
""".strip()


def build_relationship_guidance() -> str:
    return """
Relationship guidance:
- Join customers.customer_id = deposits.customer_id
- Join customers.customer_id = credits.customer_id
- Join customers.customer_id = fraud_transactions.customer_id
- One customer can have multiple deposit accounts
- One customer can have multiple credit accounts
- One customer can have multiple fraud transaction rows
- customers is the customer dimension/master table
- deposits is the account-level table used for deposit analysis
- credits is the account-level table used for credit analysis
- fraud_transactions is the transaction-level table used for fraud monitoring, anomaly analysis, and investigation
- Joining customers to deposits can duplicate customer rows because deposits is one-to-many from customers
- Joining customers to credits can duplicate customer rows because credits is one-to-many from customers
- Joining customers to fraud_transactions can duplicate customer rows because fraud_transactions is one-to-many from customers
- Joining deposits and credits together through customers can multiply rows; aggregate first when comparing both products
- Joining fraud_transactions to deposits or credits through customers can also multiply rows; aggregate each child table first when mixing account-level and transaction-level metrics
""".strip()


def build_schema_context() -> str:
    return "\n\n".join(
        (
            build_database_description(),
            build_table_descriptions(),
            build_relationship_guidance(),
        )
    )
