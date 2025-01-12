from typing import List

def batch_list(input_list: List[str], batch_size: int):
    for i in range(0, len(input_list), batch_size):
        yield input_list[i:i + batch_size]