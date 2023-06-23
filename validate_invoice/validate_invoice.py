# This is to identify that this code is for the PROD instance of ERPNext
import frappe
import csv
import json
from frappe import _
from frappe.utils import flt, fmt_money
from erpnext.selling.doctype.customer.customer import get_credit_limit, get_customer_outstanding

@frappe.whitelist(allow_guest=True)
def validate_invoice(doc, method):
    with open('/home/bitnami/stack/erpnext/frappe-bench/apps/validate_invoice/validate_invoice/checkCommonCurrencyProd.csv', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        company_currencies = {}
        for row in reader:
            company_name = row['Company Name']
            currencies = [currency.strip() for currency in row['common_currency'].split(',')]
            company_currencies[company_name] = currencies

    company_name = frappe.db.get_value('Company', doc.company, 'company_name')
    if company_name not in company_currencies:
        frappe.throw(_("Company name {0} not found in CSV. Please inform your administrator that it is required to set up the common currency configuration first in the accounting module before proceeding with creating accounting documents").format(company_name))

    currencies = company_currencies[company_name]
    if doc.currency in currencies:
        customer_accounts = frappe.db.sql("""SELECT account_currency FROM `tabAccount` as a 
                                            JOIN `tabParty Account` as pa ON pa.account = a.name 
                                            WHERE pa.parent = %s """, (doc.customer), as_dict=1)
        if customer_accounts:
            # check if any of the customer accounts are in the correct currency
            correct_currency_accounts = [account for account in customer_accounts if account.account_currency == doc.currency]
            if not correct_currency_accounts:
                frappe.throw(_("Customer does not have a default receivable account set up in {0} currency").format(doc.currency))
        else:
            frappe.throw(_("Customer does not have any account set up"))

# Function to be called before insert of a sales invoice
@frappe.whitelist()
def validate_customer_credit_and_outstanding(doc, method):
    # Get credit limit and outstanding amount for the customer
    credit_limit = get_credit_limit(doc.customer, doc.company)
    outstanding_amt = get_customer_outstanding(doc.customer, doc.company)

    # Check if the credit limit is not set
    if not credit_limit:
        # Show a message to the user
        frappe.msgprint(_("No credit limit set for the customer. The invoice is allowed to be created without checking the balance."))
    else:
        # Calculate balance
        balance = flt(credit_limit) - flt(outstanding_amt)
        
        # Calculate the total invoice amount by summing up each item's rate divided by its conversion rate
        invoice_total = sum(flt(item.item_rate) / flt(item.item_ccy_conversion) for item in doc.items)
        
        # Check if the invoice total is more than the outstanding balance
        if invoice_total >= balance:
            frappe.throw(_("Invoice total {0} is more than or equal to the available balance (Credit  Limit - Outstanding Balance) {1}").format(fmt_money(invoice_total, precision=2, currency=doc.currency), fmt_money(balance, precision=2, currency=doc.currency)))
        
        # Format numbers to a reasonable amount of decimal places (2 for currency)
        credit_limit = fmt_money(credit_limit, precision=2, currency=doc.currency)
        outstanding_amt = fmt_money(outstanding_amt, precision=2, currency=doc.currency)
        balance = fmt_money(balance, precision=2, currency=doc.currency)
        invoice_total = fmt_money(invoice_total, precision=2, currency=doc.currency)
        
        # Create the message
        message = """
        Credit Limit: {0}\n
        Outstanding Amount: {1}\n
        Outstanding Balance: {2}\n
        Invoice Total: {3}
        """.format(credit_limit, outstanding_amt, balance, invoice_total)

        # Show the message to the user
        frappe.msgprint(_(message))
