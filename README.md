DineDesk – Restaurant Management System

A restaurant operations platform built with Python Flask.

Overview

DineDesk is a full-stack restaurant management system designed to handle reservations, menu management, table status tracking, order creation, and kitchen ticket workflows.
The system was developed using Python Flask, SQLAlchemy, and Bootstrap as part of the Edinburgh Napier University module SET09103 – Advanced Web Technologies.

Features
✔ Role-Based Login

Secure authentication using Flask-Login

Different dashboards for Manager, Waiter, and Kitchen roles

✔ Dashboard

Overview of reservations, orders, and table status

Quick links to key modules

✔ Reservations

Create, edit, and delete reservations

Conflict checking to prevent double bookings

Validates date, time, table, and guest count

✔ Table Management

Displays table availability

Change table status (Available / Reserved / Occupied)

Start a new order for any table

✔ Order System

Add menu items with quantities

Automatic total calculation

Stores notes and table number

Tracks order status (Pending → In Progress → Completed)

✔ Kitchen Ticket Display

Shows all active orders

Kitchen staff can update order status

Designed for fast workflow

✔ Menu Management

Add, edit, or delete menu items

Store item name, price, category, and description

Tech Stack

Backend:

Python

Flask

Flask-Login

Flask-SQLAlchemy

Jinja2

Frontend:

HTML

CSS / Bootstrap

JavaScript

Database:

SQLite
