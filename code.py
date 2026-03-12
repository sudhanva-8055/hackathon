import pandas as pd
import json
import sys
from collections import defaultdict
import heapq
import os
# Channel configurations
CHANNELS = {
    'Channel_F': {'fee': 5.0, 'latency': 1, 'capacity': 2},
    'Channel_S': {'fee': 1.0, 'latency': 3, 'capacity': 4}, 
    'Channel_B': {'fee': 0.20, 'latency': 10, 'capacity': 10}
}

P = 0.001  # delay penalty factor
F = 0.5    # failure penalty factor

def load_transactions(filename):
    """Load and parse transactions.csv"""
    print(f"Loading transactions from: {filename}")
    df = pd.read_csv(filename)
    print(f"Loaded {len(df)} transactions")
    
    transactions = {}
    for _, row in df.iterrows():
        transactions[row['tx_id']] = {
            'amount': float(row['amount']),  # Ensure float for calculations
            'arrival_time': int(row['arrival_time']),
            'max_delay': int(row['max_delay']),
            'priority': int(row['priority']),
            'deadline': int(row['arrival_time']) + int(row['max_delay'])
        }
    return transactions

def compute_score(tx):
    """Priority score: high priority + urgent high-value transactions"""
    urgency = 1.0 / (tx['max_delay'] + 1)
    return tx['priority'] * tx['amount'] * urgency

def get_channel_usage_at_time(channel_usage, time):
    """Count active transactions at specific time for a channel"""
    count = 0
    for start_time, end_time in channel_usage.get(time, []):
        if start_time <= time < end_time:
            count += 1
    return count

def can_schedule(channel_id, start_time, duration, channel_usage):
    """Check if channel has capacity from start_time to end_time"""
    channel = CHANNELS[channel_id]
    end_time = start_time + duration
    
    # Check capacity at every minute in the slot
    for t in range(start_time, end_time):
        active_count = 0
        for existing_start, existing_end in channel_usage[channel_id]:
            if max(t, existing_start) < min(t + 1, existing_end):
                active_count += 1
        if active_count >= channel['capacity']:
            return False
    return True

def find_best_slot(tx_id, tx, channel_usage):
    """Find best (channel, start_time) minimizing cost"""
    channel_order = ['Channel_F', 'Channel_S', 'Channel_B']
    best_assignment = None
    best_cost = float('inf')
    
    # Try reasonable time window (arrival + some buffer)
    time_window = min(tx['deadline'] - tx['arrival_time'] + 10, 60)
    
    for channel_id in channel_order:
        channel = CHANNELS[channel_id]
        duration = channel['latency']
        
        for offset in range(time_window):
            start_time = tx['arrival_time'] + offset
            if start_time + duration > tx['deadline']:
                break
                
            if can_schedule(channel_id, start_time, duration, channel_usage):
                delay = start_time - tx['arrival_time']
                delay_penalty = P * tx['amount'] * delay
                total_cost = channel['fee'] + delay_penalty
                
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_assignment = (channel_id, start_time)
    
    return best_assignment

def simulate_assignment(assignments, transactions):
    """Compute total_system_cost_estimate"""
    total_cost = 0.0
    
    for tx_id, assign in assignments.items():
        if assign and assign[0]:  # Successful assignment
            channel_id, start_time = assign
            tx = transactions[tx_id]
            channel = CHANNELS[channel_id]
            
            delay = start_time - tx['arrival_time']
            delay_penalty = P * tx['amount'] * delay
            channel_fee = channel['fee']
            total_cost += channel_fee + delay_penalty
        else:  # Failed transaction
            tx = transactions[tx_id]
            total_cost += F * tx['amount']
    
    return total_cost

def smart_settle(csv_filename):
    """Main SmartSettle algorithm"""
    print(f"🚀 SmartSettle starting with: {csv_filename}")
    
    transactions = load_transactions(csv_filename)
    
    # Priority queue (max heap using negative scores)
    priority_queue = []
    for tx_id, tx in transactions.items():
        score = compute_score(tx)
        heapq.heappush(priority_queue, (-score, tx_id))
    
    channel_usage = {ch: [] for ch in CHANNELS.keys()}
    assignments = {}
    
    print("📊 Scheduling transactions...")
    while priority_queue:
        neg_score, tx_id = heapq.heappop(priority_queue)
        
        tx = transactions[tx_id]
        assignment = find_best_slot(tx_id, tx, channel_usage)
        
        if assignment:
            channel_id, start_time = assignment
            duration = CHANNELS[channel_id]['latency']
            end_time = start_time + duration
            
            channel_usage[channel_id].append((start_time, end_time))
            assignments[tx_id] = (channel_id, start_time)
            print(f"✅ {tx_id}: {channel_id} @ {start_time} (delay: {start_time-tx['arrival_time']})")
        else:
            assignments[tx_id] = None
            print(f"❌ {tx_id}: FAILED (deadline {tx['deadline']})")
    
    # Generate submission
    total_cost = simulate_assignment(assignments, transactions)
    
    output_assignments = []
    for tx_id in transactions.keys():
        if assignments[tx_id] and assignments[tx_id][0]:
            channel_id, start_time = assignments[tx_id]
            output_assignments.append({
                "tx_id": tx_id,
                "channel_id": channel_id,
                "start_time": int(start_time)
            })
        else:
            output_assignments.append({
                "tx_id": tx_id,
                "channel_id": None,
                "start_time": None,
                "failed": True
            })
    
    result = {
        "assignments": output_assignments,
        "total_system_cost_estimate": round(total_cost, 2)
    }
    
    # Save submission.json
   
    base_name = os.path.splitext(os.path.basename(csv_filename))[0]
    output_file = f"{base_name}_submission.json"

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n🎉 Submission saved: {output_file}")
    print(f"💰 Estimated total cost: ₹{total_cost:.2f}")
    print(f"✅ Success rate: {len([a for a in output_assignments if not a.get('failed')])}/{len(output_assignments)}")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python smart_settle.py <input_file.csv>")
        print("Example: python smart_settle.py trialcode.csv")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    smart_settle(csv_filename)