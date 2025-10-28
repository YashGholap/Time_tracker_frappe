# ⚙️ Time Tracker Frappe App (Server-Side API)

<p align="center"> 
  <img src="https://img.shields.io/badge/Frappe-v15+-black?style=flat-square&logo=frappe&logoColor=white" alt="Frappe Framework">
  <img src="https://img.shields.io/badge/ERPNext-Server%20Backend-black?style=flat-square&logo=erpnext&logoColor=white" alt="ERPNext Backend"> 
</p>

## Overview

This repository contains the custom Frappe application (`time_tracker`) that serves as the backend API for the **ERPNext Time Tracker Client** desktop application.

This app is responsible for:
1.  Exposing secure and filtered API endpoints to fetch data required by the desktop client (Projects, Tasks, Timesheets).
2.  Providing an authenticated endpoint to fetch the user's first name for a personalized greeting.
3.  Handling the logic for logging time entries and attaching screenshots (future planned functionality).

**⚠️ This application is required for the [ERPNext Time Tracker Client](https://github.com/YashGholap/ERPNext-Time-Tracker) to function.**

---

## 💻 Installation

To make the desktop client work, you must install this Frappe application on your ERPNext instance.

### Prerequisites

* A running instance of **ERPNext** (v13 or newer recommended).
* Bench CLI installed and configured.

### Installation Steps

1.  **Navigate to your bench directory:**
    ```bash
    cd ~/frappe-bench
    ```

2.  **Get the app from GitHub:**
    ```bash
    bench get-app [https://github.com/YashGholap/Time_tracker_frappe](https://github.com/YashGholap/Time_tracker_frappe)
    ```

3.  **Install the app on your site:**
    *(Replace `yoursite.local` with the name of your ERPNext site)*
    ```bash
    bench --site yoursite.local install-app time_tracker
    ```

4.  **Apply migrations and restart the bench:**
    ```bash
    bench migrate
    bench restart
    ```

The API endpoints will now be accessible via your ERPNext server URL.

---

## 🔗 API Endpoints

This Frappe app exposes several custom API methods that the desktop client consumes. All endpoints are secured by Frappe's authentication layer (requiring a valid **API Key** and **API Secret**).

The base path for API calls is your ERPNext server URL (e.g., `https://my.erpnext.com`).

### Core Data Endpoints

These endpoints are used primarily for the dashboard view to fetch selection options.

| Method | Description |
| :--- | :--- |
| **1. Get User First Name** | Retrieves the friendly **first name** of the currently authenticated user for the "Welcome, [Name]" message. |
| `/api/method/time_tracker.time_tracker.api.get_user_first_name` | **Returns:** A string containing the user's first name, or 'User'. |
| **2. Get Available Projects** | Fetches a list of **Projects** accessible to the authenticated user. |
| `/api/v2/method/time_tracker.time_tracker.api.get_projects` | **Returns:** A list of Project documents. |
| **3. Get Tasks for a Project** | Fetches a list of **Tasks** associated with the specified Project. |
| `/api/v2/method/time_tracker.time_tracker.api.get_tasks?project=...` | **Parameters:** `project` (URL encoded string) |
| **4. Get Draft Timesheets** | Fetches a list of **Draft Timesheets** linked to the specified Project and Task, ensuring time is logged against an existing, editable document. |
| `/api/v2/method/time_tracker.time_tracker.api.get_timesheets?project=...&task=...` | **Parameters:** `project`, `task` (URL encoded strings) |

---

### Time Log & Screenshot Endpoints

These methods handle the actual tracking, file uploads, and final submission when the user stops the timer.

| Method | Description |
| :--- | :--- |
| **5. Upload Screenshot** | Uploads a single screenshot image to the Frappe **File** Doctype immediately after capture. |
| `/api/method/time_tracker.time_tracker.api.upload_screenshot` | **Parameters:** `file_name`, `file_data` (Base64), `session_id`. **Action:** Stores the file privately and marks it with the unique `session_id` for later linking. |
| **6. Finalize Timesheet** | **Commits all tracked time intervals and attaches session screenshots.** This is the main submission endpoint. |
| `/api/method/time_tracker.time_tracker.api.finalize_timesheet_with_screenshots` | **Payload:** Includes `timesheet_name`, `task_name`, `project_name`, `intervals` (time range), and `session_id`. **Action:** Appends time rows to the Timesheet and links files sharing the `session_id` *only if* the Timesheet is configured to include screenshots. |
| **7. Cleanup Session** | Safely deletes any unlinked screenshots associated with a specific session ID. |
| `/api/method/time_tracker.time_tracker.api.cleanup_session` | **Parameters:** `session_id`. **Purpose:** Used to clear orphaned files when a tracking session is cancelled or if screenshots were not required upon finalization. |

---

## 🛠️ Contribution

We welcome contributions! If you have suggestions for improving API performance, security, or adding new features, please submit a Pull Request.