import queue

# Global queue for logs
log_queue = queue.Queue()

def log(message):
    """Send a message to the UI log box."""
    print(f"[LOG] {message}")
    log_queue.put(message)
