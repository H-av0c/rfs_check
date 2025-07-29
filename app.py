from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, func
from datetime import datetime, timezone, timedelta, date
import os
from database_headers import db, Address, UprnCheck, Whitelist, DeploymentUprn

MAX_DAILY_QUERIES = 5

app = Flask(__name__)

# Configuration for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)




# ===================================================================================================
# Display postcode capture page when app called
@app.route('/', methods=['GET', 'POST'])
def enter_postcode():
    if request.method == 'POST':
        postcode = request.form['postcode']
        addresses = Address.query.filter_by(postcode=postcode.upper()).all()
        return render_template('select_address.html', addresses=addresses, postcode=postcode.upper())
    return render_template('enter_postcode.html')




# Address check page


def store_query(requested_uprn, user_ip):
    # Log the check to web.uprn_checks
    check = UprnCheck(
        uprn=requested_uprn,
        ip_address=user_ip,
        check_date=date.today()
    )
    db.session.add(check)
    db.session.commit()


@app.route('/check_address', methods=['POST'])
def check_address():
    uprn = request.form.get('uprn')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    query_count = (
        db.session.query(func.count(UprnCheck.id))
        .outerjoin(Whitelist, UprnCheck.ip_address == Whitelist.ip_address)
        .filter(UprnCheck.check_date >= yesterday.date())
        .filter(UprnCheck.ip_address == ip_address)
        .filter(Whitelist.ip_address == None)
        .scalar()
    )


    if query_count >= MAX_DAILY_QUERIES:
        return render_template(
            "result.html",
            message="You have exceeded the maximum number of address checks allowed per day.",
            rate_limited=True
        )

    else:

        store_query(uprn, ip_address)

        # Fetch status from deployment.uprn
        deployment_status = DeploymentUprn.query.get(uprn)
        status = deployment_status.status if deployment_status else None

        # Interpret the status into a message
        STATUS_MESSAGES = {
            1: 'Good news!  We are considering building at your property.',
            2: 'Good news!  Your property is already in our plans.',
            3: 'Good news!  We are already building to connect your property.',
            4: 'Good news!  We are already building to connect your property.',
            5: 'Good news!  Your property is ready to be connected - you can order now.',
            6: 'Good news!  Your property is ready to be connected - you can order now.'
        }

        message = STATUS_MESSAGES.get(status, 'Sorry, we have no plans to build at your property at present.')

        # If the address is eligible (status = 1), allow the user to enter details
        if status:
            address = Address.query.get(uprn)
            return render_template('result.html', message=message, address=address, rate_limited=False)
        else:
            return render_template('result.html', message=message, rate_limited=False)


# Submit user details
@app.route('/submit_details', methods=['POST'])
def submit_details():
    address_id = request.form['address_id']
    user_name = request.form['user_name']
    user_email = request.form['user_email']

    address = Address.query.get(address_id)
    if address:
        address.user_name = user_name
        address.user_email = user_email
        db.session.commit()
        message = 'Your details have been saved.'
    else:
        message = 'Address not found.'
    return render_template('result.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
