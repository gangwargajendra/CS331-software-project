import datetime

def get_congestion_level(vehicle_count):
    """
    Categorizes traffic density based on vehicle count.
    """
    if vehicle_count == 0:
        return "Empty"
    elif vehicle_count < 5:
        return "Low"
    elif vehicle_count < 15:
        return "Medium"
    else:
        return "High"

def generate_session_summary(log_entries):
    """
    Creates a small text summary of the traffic session.
    """
    if not log_entries:
        return "No data recorded."
        
    total_vehicles = sum(entry['count'] for entry in log_entries)
    avg_vehicles = total_vehicles / len(log_entries)
    peak_traffic = max(entry['count'] for entry in log_entries)
    
    summary = f"--- Traffic Report {datetime.date.today()} ---\n"
    summary += f"Average Vehicle Density: {avg_vehicles:.2f}\n"
    summary += f"Peak Traffic Count: {peak_traffic}\n"
    summary += "Status: " + ("Congested" if avg_vehicles > 10 else "Flowing")
    
    return summary

if __name__ == "__main__":
    test_count = 12
    print(f"Count {test_count} is: {get_congestion_level(test_count)}")