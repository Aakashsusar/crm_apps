import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def get_active_calls():
    """Get currently active calls (Initiated, Ringing, In Progress)"""
    try:
        # Get calls that are currently active
        active_calls = frappe.get_all(
            "CRM Call Log",
            filters={
                "status": ["in", ["Initiated", "Ringing", "In Progress", "Routed"]],
                "type": "Incoming",
                "start_time": [">", datetime.now() - timedelta(hours=24)]
            },
            fields=["name", "from_field", "to", "receiver", "status", "start_time", "duration"],
            order_by="start_time desc"
        )
        
        return active_calls
    except Exception as e:
        frappe.log_error(f"Error getting active calls: {str(e)}")
        return []


@frappe.whitelist()
def get_recent_calls(time_filter="today"):
    """Get recent calls based on time filter"""
    try:
        # Calculate date range based on filter
        if time_filter == "today":
            start_date = datetime.now().date()
        elif time_filter == "yesterday":
            start_date = datetime.now().date() - timedelta(days=1)
            end_date = start_date
        elif time_filter == "week":
            start_date = datetime.now().date() - timedelta(days=7)
        elif time_filter == "month":
            start_date = datetime.now().date() - timedelta(days=30)
        else:
            start_date = datetime.now().date()
        
        end_date = datetime.now().date()
        
        # Get recent calls
        recent_calls = frappe.get_all(
            "CRM Call Log",
            filters={
                "type": "Incoming",
                "start_time": ["between", [start_date, end_date]]
            },
            fields=["name", "from_field", "to", "receiver", "status", "start_time", "duration", "note"],
            order_by="start_time desc",
            limit=50
        )
        
        return recent_calls
    except Exception as e:
        frappe.log_error(f"Error getting recent calls: {str(e)}")
        return []


@frappe.whitelist()
def get_call_queue():
    """Get current call queue statistics and queued calls"""
    try:
        # Get all queued calls
        queued_calls = frappe.get_all(
            "CRM Call Log",
            filters={
                "status": ["in", ["Queued", "Ringing", "In Progress"]],
                "type": "Incoming"
            },
            fields=["name", "from_field", "status", "start_time", "receiver"],
            order_by="start_time asc"
        )
        
        # Calculate statistics
        stats = {
            "total": len(queued_calls),
            "queued": len([call for call in queued_calls if call.status == "Queued"]),
            "ringing": len([call for call in queued_calls if call.status == "Ringing"]),
            "in_progress": len([call for call in queued_calls if call.status == "In Progress"])
        }
        
        return {
            "calls": queued_calls,
            "stats": stats
        }
    except Exception as e:
        frappe.log_error(f"Error getting call queue: {str(e)}")
        return {"calls": [], "stats": {"total": 0, "queued": 0, "ringing": 0, "in_progress": 0}}


@frappe.whitelist()
def assign_next_call():
    """Assign the next queued call to an available agent"""
    try:
        # Find the oldest queued call
        queued_call = frappe.get_all(
            "CRM Call Log",
            filters={
                "status": "Queued",
                "type": "Incoming"
            },
            fields=["name", "from_field"],
            order_by="start_time asc",
            limit=1
        )
        
        if not queued_call:
            return {"message": "No calls in queue"}
        
        call_name = queued_call[0].name
        caller_number = queued_call[0].from_field
        
        # Find available agent (simplified logic)
        available_agent = find_available_agent()
        
        if available_agent:
            # Update call status and assign to agent
            frappe.db.set_value("CRM Call Log", call_name, {
                "status": "Routed",
                "receiver": available_agent,
                "to": get_agent_number(available_agent)
            })
            
            # Update agent status
            frappe.db.set_value("User", available_agent, "call_status", "In Call")
            
            frappe.db.commit()
            
            return {
                "message": f"Call assigned to {available_agent}",
                "agent": available_agent,
                "call": call_name
            }
        else:
            return {"message": "No available agents"}
            
    except Exception as e:
        frappe.log_error(f"Error assigning next call: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def clear_completed_calls():
    """Clear completed calls from the queue view"""
    try:
        # This is more of a UI cleanup - completed calls are automatically filtered out
        # But we can update old completed calls to ensure they don't show in queue
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        frappe.db.sql("""
            UPDATE `tabCRM Call Log` 
            SET status = 'Completed' 
            WHERE status IN ('Completed', 'Failed') 
            AND start_time < %s
        """, cutoff_time)
        
        frappe.db.commit()
        
        return {"message": "Completed calls cleared"}
    except Exception as e:
        frappe.log_error(f"Error clearing completed calls: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_incoming_call_for_agent(agent):
    """Get incoming call assigned to specific agent"""
    try:
        # Find calls assigned to this agent that are ringing
        incoming_call = frappe.get_all(
            "CRM Call Log",
            filters={
                "receiver": agent,
                "status": "Routed",
                "type": "Incoming",
                "start_time": [">", datetime.now() - timedelta(minutes=5)]
            },
            fields=["name", "from_field", "start_time", "status"],
            order_by="start_time desc",
            limit=1
        )
        
        return incoming_call[0] if incoming_call else None
    except Exception as e:
        frappe.log_error(f"Error getting incoming call for agent: {str(e)}")
        return None


@frappe.whitelist()
def answer_call(call_name):
    """Mark call as answered/in progress"""
    try:
        frappe.db.set_value("CRM Call Log", call_name, {
            "status": "In Progress",
            "start_time": datetime.now()
        })
        
        # Update agent status
        call_doc = frappe.get_doc("CRM Call Log", call_name)
        if call_doc.receiver:
            frappe.db.set_value("User", call_doc.receiver, "call_status", "In Call")
        
        frappe.db.commit()
        
        return {"message": "Call answered"}
    except Exception as e:
        frappe.log_error(f"Error answering call: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def reject_call(call_name):
    """Mark call as rejected/failed"""
    try:
        frappe.db.set_value("CRM Call Log", call_name, {
            "status": "Failed",
            "end_time": datetime.now()
        })
        
        # Update agent status
        call_doc = frappe.get_doc("CRM Call Log", call_name)
        if call_doc.receiver:
            frappe.db.set_value("User", call_doc.receiver, "call_status", "Available")
        
        frappe.db.commit()
        
        return {"message": "Call rejected"}
    except Exception as e:
        frappe.log_error(f"Error rejecting call: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_agent_status(agent):
    """Get current status of an agent"""
    try:
        # Get agent's call status
        call_status = frappe.db.get_value("User", agent, "call_status") or "Available"
        
        # Check if agent is currently in a call
        current_call = frappe.get_all(
            "CRM Call Log",
            filters={
                "receiver": agent,
                "status": "In Progress",
                "type": "Incoming"
            },
            fields=["name", "from_field", "start_time", "status"],
            order_by="start_time desc",
            limit=1
        )
        
        return {
            "status": call_status,
            "current_call": current_call[0] if current_call else None
        }
    except Exception as e:
        frappe.log_error(f"Error getting agent status: {str(e)}")
        return {"status": "Available", "current_call": None}


@frappe.whitelist()
def update_agent_status(agent, status):
    """Update agent's availability status"""
    try:
        frappe.db.set_value("User", agent, "call_status", status)
        frappe.db.commit()
        
        return {"message": f"Status updated to {status}"}
    except Exception as e:
        frappe.log_error(f"Error updating agent status: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def end_call(call_name):
    """End current call and mark as completed"""
    try:
        # Update call status
        frappe.db.set_value("CRM Call Log", call_name, {
            "status": "Completed",
            "end_time": datetime.now()
        })
        
        # Update duration
        call_doc = frappe.get_doc("CRM Call Log", call_name)
        if call_doc.start_time and call_doc.end_time:
            duration = call_doc.end_time - call_doc.start_time
            frappe.db.set_value("CRM Call Log", call_name, "duration", str(duration))
        
        # Update agent status
        if call_doc.receiver:
            frappe.db.set_value("User", call_doc.receiver, "call_status", "Available")
        
        frappe.db.commit()
        
        return {"message": "Call ended"}
    except Exception as e:
        frappe.log_error(f"Error ending call: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    try:
        # Active calls
        active_calls = len(frappe.get_all(
            "CRM Call Log",
            filters={
                "status": ["in", ["Initiated", "Ringing", "In Progress", "Routed"]],
                "type": "Incoming",
                "start_time": [">", datetime.now() - timedelta(hours=24)]
            }
        ))
        
        # Queued calls
        queued_calls = len(frappe.get_all(
            "CRM Call Log",
            filters={
                "status": "Queued",
                "type": "Incoming"
            }
        ))
        
        # Completed calls today
        completed_calls = len(frappe.get_all(
            "CRM Call Log",
            filters={
                "status": "Completed",
                "type": "Incoming",
                "start_time": [">", datetime.now().date()]
            }
        ))
        
        # Available agents
        available_agents = len(frappe.get_all(
            "User",
            filters={
                "enabled": 1,
                "call_status": ["in", ["Available", None]]
            }
        ))
        
        # Agent performance (simplified)
        agent_performance = frappe.get_all(
            "User",
            filters={"enabled": 1},
            fields=["name", "full_name"],
            limit=5
        )
        
        # Add call counts for each agent
        for agent in agent_performance:
            agent["calls_today"] = len(frappe.get_all(
                "CRM Call Log",
                filters={
                    "receiver": agent.name,
                    "type": "Incoming",
                    "start_time": [">", datetime.now().date()]
                }
            ))
            agent["department"] = frappe.db.get_value("User", agent.name, "department") or "Sales"
        
        stats = {
            "active_calls": active_calls,
            "queued_calls": queued_calls,
            "completed_calls": completed_calls,
            "available_agents": available_agents
        }
        
        return {
            "stats": stats,
            "agent_performance": agent_performance
        }
    except Exception as e:
        frappe.log_error(f"Error getting dashboard summary: {str(e)}")
        return {
            "stats": {"active_calls": 0, "queued_calls": 0, "completed_calls": 0, "available_agents": 0},
            "agent_performance": []
        }


# Helper functions
def find_available_agent():
    """Find an available agent (simplified)"""
    try:
        available_agents = frappe.get_all(
            "User",
            filters={
                "enabled": 1,
                "call_status": ["in", ["Available", None]]
            },
            pluck="name"
        )
        
        return available_agents[0] if available_agents else None
    except:
        return None


def get_agent_number(agent_name):
    """Get agent's phone number"""
    try:
        # Check Smartflo Agent Mapping first
        smartflo_mapping = frappe.db.exists("Smartflo Agent Mapping", {"user": agent_name})
        if smartflo_mapping:
            agent_mapping = frappe.get_doc("Smartflo Agent Mapping", smartflo_mapping)
            return getattr(agent_mapping, 'agent_number', None)
        
        # Check user's phone numbers
        user_doc = frappe.get_doc("User", agent_name)
        return getattr(user_doc, 'mobile_no', None) or getattr(user_doc, 'phone', None)
    except:
        return None