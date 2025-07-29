#
# Functions performed to support address check
#
#
from datetime import datetime, timezone, timedelta, date
from database_headers import db, Address, UprnCheck, Whitelist, DeploymentUprn
from sqlalchemy import BigInteger, func

# ===================================================================================================
# Check quote note exceeded.  Return true if allowed.

def check_query_quota(dbase, user_ip, max_queries):
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    query_count = (
        dbase.session.query(func.count(UprnCheck.id))
        .outerjoin(Whitelist, UprnCheck.ip_address == Whitelist.ip_address)
        .filter(UprnCheck.check_date >= yesterday.date())
        .filter(UprnCheck.ip_address == user_ip)
        .filter(Whitelist.ip_address == None)
        .scalar()
    )

    if query_count < max_queries:
        allowed = True
    else:
        allowed = False

    return allowed


# ===================================================================================================
# Store the uprn and the user ip address

def store_query(dbase, requested_uprn, user_ip):
    # Log the check to web.uprn_checks
    check = UprnCheck(
        uprn=requested_uprn,
        ip_address=user_ip,
        check_date=date.today()
    )
    dbase.session.add(check)
    dbase.session.commit()

# ===================================================================================================

def get_status_message(target_uprn):
    deployment_status = DeploymentUprn.query.get(target_uprn)
    result_status = deployment_status.status if deployment_status else None

    # Interpret the status into a message
    STATUS_MESSAGES = {
        1: 'Good news!  We are considering building at your property.',
        2: 'Good news!  Your property is already in our plans.',
        3: 'Good news!  We are already building to connect your property.',
        4: 'Good news!  We are already building to connect your property.',
        5: 'Good news!  Your property is ready to be connected - you can order now.',
        6: 'Good news!  Your property is ready to be connected - you can order now.'
    }

    result_message = STATUS_MESSAGES.get(result_status, 'Sorry, we have no plans to build at your property at present.')

    return result_status, result_message