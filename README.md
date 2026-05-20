# Student Flow

Student Flow is a modern desktop task management application developed for students to organize academic activities in one workspace.

The application allows users to manage assignments, projects, exams, courses, deadlines, and track study progress through an interactive desktop interface.

---

## Project Goal

The goal of Student Flow is to help students organize their study process efficiently by providing:

* task management
* course management
* deadline tracking
* search functionality
* progress monitoring
* completed task history

The application uses a modern desktop UI and stores information locally using JSON files.

---

## Features

### Dashboard

* Overview of total tasks
* Completed tasks count
* Pending tasks count
* Course count
* Progress tracking
* Dynamic statistics cards

### Task Management

* Add new tasks
* Edit tasks
* Delete tasks
* Mark tasks as completed
* Automatic task organization

### Completed Tasks History

* Completed tasks are moved automatically
* Completion date is stored
* Separate history page

### Course Management

* Add courses
* Edit courses
* Delete courses
* Display number of tasks per course

### Search System

* Search by:

  * task title
  * course
  * task type
  * status

### Deadline Management

* Calendar date picker
* Automatic nearest deadline sorting

### Theme Support

* Dark mode
* Light mode
* Theme preferences saved automatically

---

## Technologies Used

* Python
* CustomTkinter
* JSON
* tkcalendar
* Matplotlib

---

## Programming Concepts Used

This project implements concepts studied during the course:

* Object-Oriented Programming (OOP)
* Classes and Objects
* Data Structures

  * Lists
  * Dictionaries
  * Sets
* File handling
* JSON storage
* External modules
* Decorators
* Generators
* Modular programming

---

## Project Structure

StudentFlow_Final/

main.py

task.py

task_manager.py

course_manager.py

completed_task_manager.py

theme_manager.py

utils.py

tasks.json

courses.json

completed_tasks.json

settings.json

requirements.txt

README.md

---

## Decorators Used

The project uses decorators for:

* input validation
* automatic saving
* extending function behavior without modifying original code

Examples:

* validate_deadline
* auto_save
* require_non_empty

---

## Installation

Install dependencies:

pip install -r requirements.txt

Run application:

python main.py

---

## Author
Absultanov Nurdaulet
Toleumuratova Aisamal


Final Project

Introduction to Programming 2

Student Flow
