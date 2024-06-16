from planner import step_decomposer
from executor import get_response, verify_response
  
LOG_FILE = 'execution_log.txt'  
  
def log_to_file(text, file = LOG_FILE):  
    with open(file, 'a') as file:  
        file.write(text + '\n\n')  


def execute_step(step, logic):  
    result = get_response(query=step)
    verify = verify_response(query=f"Q: {step}\nA: {result}")
    log_to_file(f"Q: {step}")
    log_to_file(f"A: {result}")  
    log_to_file(f"V: {verify}")
    if verify == "False":
        return None
    log_to_file(f"Q: {step}\nA: {result}", file="extracted_data.txt")
    return result  



def controller(plan, depth=3):  
    if isinstance(plan, dict):  
  
        steps = plan.get('steps', [])  
        logic = plan.get('logic', 'AND')  
  
        # log_to_file(f"Controller at depth {depth}: Executing plan with {logic} logic.")  
  
        results = []  
        for index, step in enumerate(steps):  
  
            if isinstance(step, str):  
  
                # log_to_file(f"Controller at depth {depth}: Executing step: {step}")  
                result = execute_step(step, logic)  
                if result is None and depth > 0:  
  
                    # log_to_file(f"Controller at depth {depth}: Step failed, replanning for step: {step}")  
                    # new_plan = planner(step)  
                    new_plan = step_decomposer(failed_step=step)  
  
                    log_to_file(f"NEW PLAN: {new_plan}")  
                    result = controller(new_plan, depth - 1)  # Decrement the depth  
                results.append(result)  
            elif isinstance(step, dict):  
  
                result = controller(step, depth - 1 if depth > 0 else depth)  # Decrement the depth only if above zero  
                if result is None and logic == 'AND':  
  
                    # log_to_file(f"Controller at depth {depth}: Sub-plan failed with AND logic.")  
                    return None  
                results.append(result)  
  
            if logic == 'OR' and result is not None:  
  
                # log_to_file(f"Controller at depth {depth}: Successful result with OR logic.")  
                return results  
  
        # log_to_file(f"Controller at depth {depth}: Completed execution of plan.")  
        return results if logic == 'AND' else None  
    else:  
  
        raise ValueError("Invalid plan format")  


  
# Clear log file before starting a new execution  
with open(LOG_FILE, 'w') as file:  
    pass  
  