# This file has all the API's for the time tracker app
import frappe, base64, uuid
import json
from frappe.utils import now_datetime
from datetime import datetime


def parse_datetime_naive(dt_str):
    """
    Convert ISO 8601 datetime string to offset-naive datetime.
    """
    if not dt_str:
        return None
    dt = frappe.utils.get_datetime(dt_str)  # this preserves timezone if present
    # Remove timezone info to make it naive
    return dt.replace(tzinfo=None)

@frappe.whitelist()
def get_projects():
    """
    Get's all the projects with respect to the user
    """
    try:
        projects = frappe.get_list(
            "Project",
            filters={"status":"Open"},
            fields=["name", "project_name"]
        )
        return projects
    except Exception as e:
        frappe.log_error(title="Time Tracker: Error fetching projects", message=f"Traceback:\n{frappe.get_traceback()}")
        return {"error": str(e)}


@frappe.whitelist()
def get_tasks(project):
    """
    Get's all the tasks for a given project
    """
    try:
        tasks = frappe.get_list(
            "Task",
            filters=[
                ["project", "=", project],
                ["status", "not in", ["Completed", "Cancelled"]]
                ],
            fields=["name", "subject"]
        )
        return tasks
    except Exception as e:
        frappe.log_error(title="Time Tracker: Error fetching tasks", message=f"Traceback:\n{frappe.get_traceback()}")
        return {"error": str(e)}
    
@frappe.whitelist()
def get_timesheets(project, task):
    """
    Get's all the timesheets for a given project and task
    """
    try:
        timesheets = frappe.get_list(
            "Timesheet",
            filters={
                "parent_project" : project,
                "custom_task" : task,
                "docstatus": 0
            },
            fields=["name"]
        )
        return timesheets
    except Exception as e:
        frappe.log_error(title="Time Tracker: Error fetching timesheets", message=f"Traceback:\n{frappe.get_traceback()}")
        return {"error": str(e)}
    

@frappe.whitelist()
def save_timesheet_with_screenshots(data):
    """
    Temporary handler – just log everything received
    """
    frappe.log_error(
        title="Time Tracker: Data received",
        message=frappe.as_json(data, indent=2)
    )
    return {"status": "ok", "received": True}


@frappe.whitelist()
def upload_screenshot(file_name, file_data, session_id):
    """
    Uploads a screenshot immediately with custom_session_id.
    file data is a base64 without the data:image/png;base64, prefix.
    """
    try:
        # Decode the base64 file data
        content = base64.b64decode(file_data)
        
        # Save the file in Frappe's file system
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "is_private": 1,
            "content": content
        })
        file_doc.insert()
        
        #set custom_session_id
        file_doc.db_set("custom_session_id", session_id)
        
        return {
            "file_url": file_doc.file_url,
            "session_id": session_id
        }
    except Exception as e:
        frappe.log_error(title="Time Tracker: Error uploading screenshot", message=f"Traceback:\n{frappe.get_traceback()}")
        return {"error": str(e)}
    
@frappe.whitelist(allow_guest=False)
def finalize_timesheet_with_screenshots():
    """
    Finalize a Timesheet by appending child table rows for each interval from the payload.
    Also ensures that Activity Types exist before adding rows.

    Payload (POST) expects:
    {
        "timesheet_name": "TS-2025-00001",
        "task_name": "TASK-2025-00001",
        "project_name": "PROJ-0001",
        "activity_name": "Communication",
        "intervals": [
            {"from": "2025-09-21T17:48:56", "to": "2025-09-21T18:48:56", "completed": true}
        ],
        "session_id": "uuid-session-id"
    }

    Child table 'time_logs' fields populated:
    - activity_type
    - from_time
    - to_time
    - task
    - project
    - completed (1)

    Returns:
        dict: status and number of rows added
    """
    try:
        data = frappe.form_dict.get("data")
        if not data:
            frappe.throw("Missing payload data")

        payload = json.loads(data)
        timesheet_name = payload.get("timesheet_name")
        if not timesheet_name:
            frappe.throw("Missing 'timesheet_name' in payload")

        task_name = payload.get("task_name")
        project_name = payload.get("project_name")
        activity_name = payload.get("activity_name") or "Misc"
        intervals = payload.get("intervals", [])

        timesheet = frappe.get_doc("Timesheet", timesheet_name)
        rows_added = 0

        frappe.log_error(title="Timesheet Update Started",
                         message=f"Updating Timesheet '{timesheet_name}' with {len(intervals)} intervals at {now_datetime()}")

        for interval in intervals:
            from_time = parse_datetime_naive(interval.get("from"))
            to_time = parse_datetime_naive(interval.get("to"))
            
            if not from_time or not to_time:
                frappe.log_error(title="Skipping Interval",
                                 message=f"Interval missing from/to: {interval}")
                continue

            # Ensure Activity Type exists
            if not frappe.get_all("Activity Type", filters={"activity_type": activity_name}):
                frappe.get_doc({
                    "doctype": "Activity Type",
                    "activity_type": activity_name
                }).insert(ignore_permissions=True)
                frappe.log_error(title="Activity Created",
                                 message=f"Created Activity Type '{activity_name}'")

            # Append child row
            timesheet.append("time_logs", {
                "activity_type": activity_name,
                "from_time": from_time,
                "to_time": to_time,
                "task": task_name,
                "project": project_name,
                "completed": 1
            })
            rows_added += 1
            

        timesheet.save(ignore_permissions=True)

        #--------------Attach screenshots to timesheet----------------
        session_id = payload.get("session_id")
        if session_id:
            upload_files = frappe.get_all(
                "File",
                filters={"custom_session_id": session_id },
                fields=["name"]
            )
            for file in upload_files:
                frappe.db.set_value("File",file["name"],"attached_to_doctype","Timesheet")
                frappe.db.set_value("File",file["name"],"attached_to_name",timesheet_name)
            frappe.db.commit()
        #-------------------------------------------------------------

        frappe.log_error(title="Timesheet Updated",
                         message=f"Timesheet '{timesheet_name}' updated successfully. {rows_added} intervals added.")

        # return the full url for frontend
        timesheet_url = frappe.utils.get_url_to_form("Timesheet", timesheet_name)
        return {"status": "success", "rows_added": rows_added, "timesheet_url": timesheet_url}

    except Exception as e:
        frappe.log_error(title="Timesheet Update Failed", message=str(e))
        frappe.throw(f"Failed to finalize timesheet: {str(e)}")


@frappe.whitelist()
def cleanup_session(session_id):
    """
    Safely delete screenshots belonging to a session_id if they are NOT attached to any Timesheet.
    """
    try:
        # Only delete files not attached to any doctype
        files = frappe.get_all(
            "File",
            filters={"custom_session_id": session_id},
            fields=["name","attached_to_name", "attached_to_doctype"]
        )
        deleted_count = 0
        for file in files:
            if not file.get("attached_to_doctype") and not file.get("attached_to_name"):
                frappe.delete_doc("File", file["name"], ignore_permissions=True)
                deleted_count += 1

        frappe.log_error(
            title="Cleanup Session",
            message=f"Deleted {deleted_count} unlinked screenshots for session_id: {session_id}"
        )

        return {"status": "cleaned", "deleted": deleted_count}

    except Exception as e:
        frappe.log_error(
            title="Cleanup Session Error",
            message=f"Error deleting screenshots for session_id {session_id}: {str(e)}\nTraceback:\n{frappe.get_traceback()}"
        )
        return {"error": str(e)}
