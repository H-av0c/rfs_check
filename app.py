from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, func
from datetime import datetime, timezone, timedelta, date
import os
import re
from database_headers import db, Address, UprnCheck, Whitelist, DeploymentUprn, UserDetails
from address_check import check_query_quota, store_query, get_status_message

MAX_DAILY_QUERIES = 5

app = Flask(__name__)

# Configuration for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ===================================================================================================

def format_postcode(raw_postcode):
    if not raw_postcode:
        return None

    # Strip spaces and make uppercase
    cleaned = re.sub(r'\s+', '', raw_postcode).upper()

    # Valid UK postcodes are minimum 5, max 7 characters
    if len(cleaned) < 5 or len(cleaned) > 7:
        return None  # Or raise a ValueError

    # Insert space before last 3 characters
    return cleaned[:-3] + ' ' + cleaned[-3:]


def format_addresses(addresses):
    """
    Takes a list of address objects with address1 and address2 fields,
    and returns a list of clean display strings.
    """
    combined = []

    for addr in addresses:
        if addr.address2:
            full = f"{addr.address1}, {addr.address2}"
        else:
            full = addr.address1
        combined.append((addr.uprn, full))  # Keep UPRN for form value
    return combined

# ===================================================================================================
# Display postcode capture page when app called
@app.route('/', methods=['GET', 'POST'])
def enter_postcode():
    if request.method == 'POST':
        raw_postcode = request.form['postcode']
        postcode = format_postcode(raw_postcode)


        if not postcode:
            return render_template('enter_postcode.html', error="Invalid postcode format")

        raw_addresses = Address.query.filter_by(postcode=postcode).all()
        addresses = format_addresses(raw_addresses)
        return render_template('select_address.html', addresses=addresses, postcode=postcode)
    return render_template('enter_postcode.html')


# ===================================================================================================
# Process the address checking

@app.route('/check_address', methods=['POST'])
def check_address():
    uprn = request.form.get('uprn')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    query_allowed = check_query_quota(db, ip_address, MAX_DAILY_QUERIES)

    if query_allowed == False:
        return render_template(
            "result.html",
            message="You have exceeded the maximum number of address checks allowed per day.",
            rate_limited=True
        )
    else:
        store_query(db, uprn, ip_address)
        # Fetch status from deployment.uprn

        status, message = get_status_message(uprn)

        # If the address is eligible (status = 1), allow the user to enter details
        if status:
            address = Address.query.get(uprn)
            return render_template('result.html', message=message, address=address, rate_limited=False)
        else:
            return render_template('result.html', message=message, rate_limited=False)


# ===================================================================================================
# Submit user details
@app.route('/submit_details', methods=['POST'])
def submit_details():
    uprn = request.form.get('uprn')
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    user = UserDetails(
        uprn=uprn,
        name=name,
        email=email,
        phone=phone,
        date=date.today()
    )

    db.session.add(user)
    db.session.commit()

    return render_template('result.html', message='Your details have been saved successfully.')


if __name__ == '__main__':
    app.run(debug=True)
