import yaml
from pathlib import Path

def load_role(filename):
    """yaml파일로부터 agent의 역할을 불러오는 메서드."""
    current_path = Path(__file__)
    role_path = current_path.parents[1] / 'roles' / filename
    with open(role_path, 'r', encoding='utf-8') as f:
        role = yaml.safe_load(f)
    return role
