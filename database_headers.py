from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, String, Date
from sqlalchemy.orm import declarative_base

db = SQLAlchemy()


# Module to Define the database models


# ===================================================================================================
# Header to retrieve address1 and uprn from a given postcode

class Address(db.Model):
    __tablename__ = 'uprn'  # Assumes table already exists
    __table_args__ = {'schema': 'public'}
    uprn = db.Column(db.BigInteger, primary_key=True)
    postcode = db.Column(db.String, nullable=False)
    address1 = db.Column(db.String, nullable=False)
    address2 = db.Column(db.String, nullable=False)


# ===================================================================================================
# Header to retrieve build status for a uprn

class DeploymentUprn(db.Model):
    __tablename__ = 'build_uprns'
    __table_args__ = {'schema': 'deployment'}
    uprn = db.Column(db.BigInteger, primary_key=True)
    status = db.Column(db.SmallInteger)  # adjust type based on your actual table


# ===================================================================================================
# Header to handle whitelisted IP addresses

class Whitelist(db.Model):
    __tablename__ = 'whitelist'
    __table_args__ = {'schema': 'web'}

    ip_address = db.Column(db.String, primary_key=True)


# ===================================================================================================
# Header to check count - add to check and for anti-spam check

class UprnCheck(db.Model):
    __tablename__ = 'uprn_checks'
    __table_args__ = {'schema': 'web'}

    id = db.Column(db.BigInteger, primary_key=True)
    uprn = db.Column(db.BigInteger)
    ip_address = db.Column(db.String)  # SQLAlchemy doesn’t support `inet` natively
    check_date = db.Column(db.Date, nullable=False)


# ===================================================================================================
# Header to capture user data

class UserDetails(db.Model):
    __tablename__ = 'user_details'
    __table_args__ = {'schema': 'web'}

    id = db.Column(db.BigInteger, primary_key=True)
    uprn = db.Column(db.BigInteger)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date = db.Column(db.Date)


